"""Administrative reporting and metrics endpoints."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Gauge, generate_latest
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..dependencies.auth import require_roles
from ..services import audit as audit_service

admin_access = require_roles("admin", "staff")

metrics_router = APIRouter(prefix="/api/v1/admin", tags=["admin-metrics"])
reports_router = APIRouter(prefix="/api/v1/admin/reports", tags=["admin-reports"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _log_export(
    db: Session,
    *,
    actor_id: int,
    resource: str,
    extra: dict[str, int | float | str] | None = None,
) -> None:
    audit_service.record_audit(
        db,
        actor_id=actor_id,
        action="export",
        entity_type="report",
        entity_id=resource,
        metadata={"resource": resource, **(extra or {})},
    )
    db.commit()


@metrics_router.get("/metrics")
def prometheus_metrics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_access),
) -> Response:
    """Return a Prometheus compatible metrics payload for administrators."""

    registry = CollectorRegistry()

    total_users = (
        db.query(func.count(models.User.user_id))
        .filter(models.User.deleted_at.is_(None))
        .scalar()
        or 0
    )
    Gauge(
        "lost_and_found_users_total",
        "Total number of active (non-deleted) users.",
        registry=registry,
    ).set(total_users)

    active_users = (
        db.query(func.count(models.User.user_id))
        .filter(models.User.deleted_at.is_(None), models.User.is_disabled.is_(False))
        .scalar()
        or 0
    )
    Gauge(
        "lost_and_found_users_active",
        "Count of users enabled for login.",
        registry=registry,
    ).set(active_users)

    total_items = (
        db.query(func.count(models.Item.item_id))
        .filter(models.Item.deleted_at.is_(None))
        .scalar()
        or 0
    )
    Gauge(
        "lost_and_found_items_total",
        "Total number of catalogued items.",
        registry=registry,
    ).set(total_items)

    open_cases = (
        db.query(func.count(models.Case.found_id))
        .filter(models.Case.deleted_at.is_(None), models.Case.case_close_at.is_(None))
        .scalar()
        or 0
    )
    Gauge(
        "lost_and_found_cases_open",
        "Number of cases that are still open.",
        registry=registry,
    ).set(open_cases)

    boxes_with_open_cases = (
        db.query(func.count(func.distinct(models.Case.box_id)))
        .filter(
            models.Case.deleted_at.is_(None),
            models.Case.case_close_at.is_(None),
            models.Case.box_id.isnot(None),
        )
        .scalar()
        or 0
    )
    Gauge(
        "lost_and_found_boxes_with_open_cases",
        "Number of boxes currently storing at least one open case.",
        registry=registry,
    ).set(boxes_with_open_cases)

    payload = generate_latest(registry)

    _log_export(
        db,
        actor_id=current_user.user_id,
        resource="admin_metrics_prometheus",
        extra={
            "total_users": total_users,
            "total_items": total_items,
            "open_cases": open_cases,
        },
    )

    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


@reports_router.get("/overview", response_model=schemas.OverviewReport)
def overview_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_access),
) -> schemas.OverviewReport:
    """Aggregate high-level KPIs across users, items, cases and boxes."""

    now = _utcnow()

    total_users = (
        db.query(func.count(models.User.user_id))
        .filter(models.User.deleted_at.is_(None))
        .scalar()
        or 0
    )
    disabled_users = (
        db.query(func.count(models.User.user_id))
        .filter(
            models.User.deleted_at.is_(None),
            models.User.is_disabled.is_(True),
        )
        .scalar()
        or 0
    )
    deleted_users = (
        db.query(func.count(models.User.user_id))
        .filter(models.User.deleted_at.isnot(None))
        .scalar()
        or 0
    )

    users_metrics = schemas.OverviewUsersMetrics(
        total=total_users,
        active=total_users - disabled_users,
        disabled=disabled_users,
        deleted=deleted_users,
    )

    active_items = (
        db.query(func.count(models.Item.item_id))
        .filter(models.Item.deleted_at.is_(None))
        .scalar()
        or 0
    )
    deleted_items = (
        db.query(func.count(models.Item.item_id))
        .filter(models.Item.deleted_at.isnot(None))
        .scalar()
        or 0
    )
    status_rows = (
        db.query(func.coalesce(models.Item.status, "unknown"), func.count())
        .filter(models.Item.deleted_at.is_(None))
        .group_by(func.coalesce(models.Item.status, "unknown"))
        .all()
    )
    items_by_status = {status: count for status, count in status_rows}

    items_metrics = schemas.OverviewItemsMetrics(
        total=active_items,
        deleted=deleted_items,
        by_status=items_by_status,
    )

    total_cases = (
        db.query(func.count(models.Case.found_id))
        .filter(models.Case.deleted_at.is_(None))
        .scalar()
        or 0
    )
    closed_cases = (
        db.query(func.count(models.Case.found_id))
        .filter(
            models.Case.deleted_at.is_(None),
            models.Case.case_close_at.isnot(None),
        )
        .scalar()
        or 0
    )
    open_cases = total_cases - closed_cases

    cutoff = now - timedelta(days=30)
    recently_closed = (
        db.query(func.count(models.Case.found_id))
        .filter(
            models.Case.deleted_at.is_(None),
            models.Case.case_close_at.isnot(None),
            models.Case.case_close_at >= cutoff,
        )
        .scalar()
        or 0
    )

    avg_resolution_days = (
        db.query(
            func.avg(
                func.julianday(models.Case.case_close_at)
                - func.julianday(models.Case.created_at)
            )
        )
        .filter(
            models.Case.deleted_at.is_(None),
            models.Case.case_close_at.isnot(None),
        )
        .scalar()
    )
    avg_resolution_hours = (
        float(avg_resolution_days * 24) if avg_resolution_days is not None else None
    )

    cases_metrics = schemas.OverviewCasesMetrics(
        total=total_cases,
        open=open_cases,
        closed=closed_cases,
        closed_last_30_days=recently_closed,
        average_resolution_hours=avg_resolution_hours,
    )

    boxes = db.query(models.Box).all()
    case_assignments = (
        db.query(models.Case.box_id, models.Case.case_close_at)
        .filter(
            models.Case.deleted_at.is_(None),
            models.Case.box_id.isnot(None),
        )
        .all()
    )
    cases_per_box: dict[int, dict[str, int]] = defaultdict(lambda: {"total": 0, "active": 0})
    for box_id, case_close_at in case_assignments:
        if box_id is None:
            continue
        bucket = cases_per_box[box_id]
        bucket["total"] += 1
        if case_close_at is None:
            bucket["active"] += 1

    boxes_available = sum(1 for box in boxes if box.status is True)
    boxes_unavailable = sum(1 for box in boxes if box.status is False)
    boxes_unknown = len(boxes) - boxes_available - boxes_unavailable
    boxes_with_active_cases = sum(1 for stats in cases_per_box.values() if stats["active"] > 0)
    boxes_with_load = [box.load for box in boxes if box.load is not None]
    average_load = (
        float(sum(boxes_with_load) / len(boxes_with_load)) if boxes_with_load else None
    )
    door_open = sum(1 for box in boxes if box.door_status)

    boxes_metrics = schemas.OverviewBoxesMetrics(
        total=len(boxes),
        available=boxes_available,
        unavailable=boxes_unavailable,
        unknown=boxes_unknown,
        with_active_cases=boxes_with_active_cases,
        average_load=average_load,
        doors_open=door_open,
    )

    report = schemas.OverviewReport(
        generated_at=now,
        users=users_metrics,
        items=items_metrics,
        cases=cases_metrics,
        boxes=boxes_metrics,
    )

    _log_export(
        db,
        actor_id=current_user.user_id,
        resource="admin_report_overview",
        extra={
            "total_users": report.users.total,
            "total_items": report.items.total,
            "total_cases": report.cases.total,
        },
    )

    return report


@reports_router.get(
    "/boxes-utilization", response_model=schemas.BoxUtilizationReport
)
def boxes_utilization_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_access),
) -> schemas.BoxUtilizationReport:
    """Provide per-box utilization metrics for operations staff."""

    now = _utcnow()

    boxes = db.query(models.Box).all()
    case_assignments = (
        db.query(models.Case.box_id, models.Case.case_close_at)
        .filter(
            models.Case.deleted_at.is_(None),
            models.Case.box_id.isnot(None),
        )
        .all()
    )

    cases_per_box: dict[int, dict[str, int]] = defaultdict(lambda: {"total": 0, "active": 0})
    for box_id, case_close_at in case_assignments:
        if box_id is None:
            continue
        bucket = cases_per_box[box_id]
        bucket["total"] += 1
        if case_close_at is None:
            bucket["active"] += 1

    entries: list[schemas.BoxUtilizationEntry] = []
    total_cases = 0
    active_cases = 0
    loads: list[int] = []
    doors_open = 0
    active_boxes = 0

    for box in boxes:
        stats = cases_per_box.get(box.box_id, {"total": 0, "active": 0})
        total_cases += stats["total"]
        active_cases += stats["active"]
        if box.load is not None:
            loads.append(box.load)
        if box.door_status:
            doors_open += 1
        if box.status is True:
            active_boxes += 1

        utilization_rate = float(box.load) / 100.0 if box.load is not None else None

        entries.append(
            schemas.BoxUtilizationEntry(
                box_id=box.box_id,
                location=box.location,
                status=box.status,
                load=box.load,
                door_status=box.door_status,
                last_accessed=box.last_accessed,
                total_cases=stats["total"],
                active_cases=stats["active"],
                utilization_rate=utilization_rate,
            )
        )

    average_load = float(sum(loads) / len(loads)) if loads else None

    totals = schemas.BoxUtilizationTotals(
        total_boxes=len(boxes),
        active_boxes=active_boxes,
        doors_open=doors_open,
        total_cases=total_cases,
        active_cases=active_cases,
        average_load=average_load,
    )

    report = schemas.BoxUtilizationReport(
        generated_at=now,
        totals=totals,
        boxes=entries,
    )

    _log_export(
        db,
        actor_id=current_user.user_id,
        resource="admin_report_boxes_utilization",
        extra={
            "total_boxes": totals.total_boxes,
            "active_cases": totals.active_cases,
        },
    )

    return report

