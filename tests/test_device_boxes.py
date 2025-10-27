from __future__ import annotations

from datetime import datetime, timezone

from fastapi import status

from app import models


def _create_box(session, *, status_value=True, door_status=False) -> models.Box:
    box = models.Box(
        status=status_value,
        location="Test Bay",
        load=0,
        door_status=door_status,
    )
    session.add(box)
    session.commit()
    session.refresh(box)
    return box


def test_deposit_to_pickup_flow(client, db_session):
    box = _create_box(db_session, status_value=True, door_status=False)

    unlock_response = client.post(
        f"/api/v1/boxes/{box.box_id}/deposit/unlock",
        json={"request_id": "req-1", "device_id": "esp32-01"},
    )
    assert unlock_response.status_code == status.HTTP_200_OK
    unlock_payload = unlock_response.json()
    assert unlock_payload["door_status"] is True
    db_session.refresh(box)
    assert box.door_status is True

    complete_response = client.post(
        f"/api/v1/boxes/{box.box_id}/deposit/complete",
        json={"request_id": "req-2", "load": 1, "door_closed": True},
    )
    assert complete_response.status_code == status.HTTP_200_OK
    complete_payload = complete_response.json()
    assert complete_payload["box_status"] is False
    assert complete_payload["door_status"] is False

    user = models.User(
        name="Collector",
        email="collector@example.com",
        role="user",
        password="secret",
        rfid_tag="RF123",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    validate_response = client.post(
        f"/api/v1/boxes/{box.box_id}/pickup/validate",
        json={"request_id": "req-3", "rfid_uid": "RF123"},
    )
    assert validate_response.status_code == status.HTTP_200_OK
    validate_payload = validate_response.json()
    assert validate_payload["door_status"] is True
    assert validate_payload["user_id"] == user.user_id

    photo_time = datetime.now(timezone.utc).isoformat()
    complete_pickup = client.post(
        f"/api/v1/boxes/{box.box_id}/pickup/complete",
        json={
            "request_id": "req-4",
            "rfid_uid": "RF123",
            "photo_url": "https://example.com/photo.jpg",
            "photo_taken_at": photo_time,
        },
    )
    assert complete_pickup.status_code == status.HTTP_200_OK
    complete_pickup_payload = complete_pickup.json()
    assert complete_pickup_payload["box_status"] is True
    assert complete_pickup_payload["door_status"] is False
    assert complete_pickup_payload["user_id"] == user.user_id
    assert complete_pickup_payload["metadata"]["photo_url"] == "https://example.com/photo.jpg"

    audit_entries = (
        db_session.query(models.AuditLog)
        .filter(
            models.AuditLog.entity_type == "box",
            models.AuditLog.entity_id == str(box.box_id),
        )
        .count()
    )
    assert audit_entries == 4
    telemetry_entries = (
        db_session.query(models.BoxTelemetry)
        .filter_by(box_id=box.box_id)
        .order_by(models.BoxTelemetry.telemetry_id)
        .all()
    )
    assert len(telemetry_entries) == 4
    assert telemetry_entries[0].payload["event"] == "deposit_unlock"
    assert telemetry_entries[-1].payload["event"] == "pickup_complete"


def test_rejection_paths(client, db_session):
    unavailable_box = _create_box(db_session, status_value=False, door_status=False)
    response = client.post(
        f"/api/v1/boxes/{unavailable_box.box_id}/deposit/unlock",
        json={"request_id": "req-a"},
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    closed_box = _create_box(db_session, status_value=True, door_status=False)
    response = client.post(
        f"/api/v1/boxes/{closed_box.box_id}/deposit/complete",
        json={"request_id": "req-b"},
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    full_box = _create_box(db_session, status_value=False, door_status=False)
    response = client.post(
        f"/api/v1/boxes/{full_box.box_id}/pickup/validate",
        json={"request_id": "req-c", "rfid_uid": "missing"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client.post(
        f"/api/v1/boxes/{full_box.box_id}/pickup/complete",
        json={"request_id": "req-d"},
    )
    assert response.status_code == status.HTTP_409_CONFLICT


def test_timeout_logging(client, db_session):
    box = _create_box(db_session, status_value=False, door_status=False)
    timeout_response = client.post(
        f"/api/v1/boxes/{box.box_id}/door-timeout",
        json={"request_id": "req-time", "duration_seconds": 90, "door_open": True},
    )
    assert timeout_response.status_code == status.HTTP_200_OK
    payload = timeout_response.json()
    assert payload["door_status"] is True

    activity_response = client.post(
        f"/api/v1/boxes/{box.box_id}/activity",
        json={"request_id": "req-act", "triggered": True, "sensor_value": 512},
    )
    assert activity_response.status_code == status.HTTP_200_OK
    activity_payload = activity_response.json()
    assert activity_payload["metadata"]["sensor_value"] == 512

    audit_count = (
        db_session.query(models.AuditLog)
        .filter(
            models.AuditLog.entity_type == "box",
            models.AuditLog.entity_id == str(box.box_id),
        )
        .count()
    )
    assert audit_count == 2
    telemetry_events = [
        t.payload["event"]
        for t in db_session.query(models.BoxTelemetry)
        .order_by(models.BoxTelemetry.telemetry_id)
        .all()
    ]
    assert telemetry_events == ["door_timeout", "infrared_activity"]
