from flask import Blueprint, jsonify, request

from database import create_box, get_box, list_boxes, update_box

box_bp = Blueprint("box", __name__)


def _to_bool(value):
    if value is None:
        return None
    return bool(value)


@box_bp.route("/box/register", methods=["POST"])
def register_box():
    data = request.get_json() or {}
    location = (data.get("location") or "").strip()
    if not location:
        return jsonify({"error": "location is required"}), 400

    status = data.get("status", True)
    door_status = data.get("door_status", False)
    load = data.get("load", 0)

    try:
        load_value = int(load)
    except (TypeError, ValueError):
        return jsonify({"error": "load must be an integer"}), 400

    try:
        box_id = create_box(
            location=location,
            status=bool(status),
            door_status=bool(door_status),
            load=load_value,
        )
        return (
            jsonify(
                {
                    "message": "Box registered successfully",
                    "box_id": box_id,
                    "location": location,
                    "status": bool(status),
                    "door_status": bool(door_status),
                    "load": load_value,
                }
            ),
            201,
        )
    except Exception as exc:  # pragma: no cover - sqlite safety net
        return jsonify({"error": f"Failed to register box: {exc}"}), 500


@box_bp.route("/box/status", methods=["GET"])
def get_box_info():
    box_id = request.args.get("box_id")
    if not box_id:
        return jsonify({"error": "box_id query parameter is required"}), 400

    try:
        box_id = int(box_id)
    except (TypeError, ValueError):
        return jsonify({"error": "box_id must be an integer"}), 400

    box = get_box(box_id)
    if not box:
        return jsonify({"error": f"Box with id '{box_id}' not found"}), 404

    return jsonify(
        {
            "box_id": box["box_id"],
            "status": _to_bool(box["status"]),
            "door_status": _to_bool(box["door_status"]),
            "location": box["location"],
            "load": box["load"],
            "last_accessed": box["last_accessed"],
        }
    )


@box_bp.route("/box/status", methods=["POST"])
def update_box_info():
    box_id = request.args.get("box_id")
    if not box_id:
        return jsonify({"error": "box_id query parameter is required"}), 400

    try:
        box_id = int(box_id)
    except (TypeError, ValueError):
        return jsonify({"error": "box_id must be an integer"}), 400

    data = request.get_json() or {}
    if not data:
        return jsonify({"error": "No data provided"}), 400

    status = data.get("status")
    door_status = data.get("door_status")
    location = data.get("location")
    load = data.get("load")

    if all(value is None for value in (status, door_status, location, load)):
        return jsonify({"error": "No updatable fields provided"}), 400

    load_value = None
    if load is not None:
        try:
            load_value = int(load)
        except (TypeError, ValueError):
            return jsonify({"error": "load must be an integer"}), 400

    updated = update_box(
        box_id,
        status=bool(status) if status is not None else None,
        door_status=bool(door_status) if door_status is not None else None,
        location=location,
        load=load_value,
    )

    if updated == 0:
        return jsonify({"error": f"Box with id '{box_id}' not found"}), 404

    refreshed = get_box(box_id)
    return jsonify(
        {
            "message": "Box updated successfully",
            "box_id": refreshed["box_id"],
            "status": _to_bool(refreshed["status"]),
            "door_status": _to_bool(refreshed["door_status"]),
            "location": refreshed["location"],
            "load": refreshed["load"],
            "last_accessed": refreshed["last_accessed"],
            "is_empty": int(refreshed["load"] or 0) == 0,
            "is_occupied": int(refreshed["load"] or 0) > 0,
            "door_open": bool(refreshed["door_status"]),
        }
    )


@box_bp.route("/box/open", methods=["POST"])
def open_box():
    data = request.get_json() or {}
    box_id = data.get("box_id")
    if not box_id:
        return jsonify({"error": "box_id is required"}), 400

    try:
        box_id = int(box_id)
    except (TypeError, ValueError):
        return jsonify({"error": "box_id must be an integer"}), 400

    updated = update_box(box_id, door_status=True)
    if updated == 0:
        return jsonify({"error": f"Box with id '{box_id}' not found"}), 404

    box = get_box(box_id)
    return jsonify(
        {
            "message": "Box opened successfully",
            "box_id": box["box_id"],
            "door_status": _to_bool(box["door_status"]),
            "last_accessed": box["last_accessed"],
        }
    )


@box_bp.route("/box/close", methods=["POST"])
def close_box():
    data = request.get_json() or {}
    box_id = data.get("box_id")
    if not box_id:
        return jsonify({"error": "box_id is required"}), 400

    try:
        box_id = int(box_id)
    except (TypeError, ValueError):
        return jsonify({"error": "box_id must be an integer"}), 400

    updated = update_box(box_id, door_status=False)
    if updated == 0:
        return jsonify({"error": f"Box with id '{box_id}' not found"}), 404

    box = get_box(box_id)
    return jsonify(
        {
            "message": "Box closed successfully",
            "box_id": box["box_id"],
            "door_status": _to_bool(box["door_status"]),
            "last_accessed": box["last_accessed"],
        }
    )


@box_bp.route("/box/all", methods=["GET"])
def get_boxes():
    boxes = list_boxes()
    payload = [
        {
            "box_id": box["box_id"],
            "status": _to_bool(box["status"]),
            "door_status": _to_bool(box["door_status"]),
            "location": box["location"],
            "load": box["load"],
            "last_accessed": box["last_accessed"],
        }
        for box in boxes
    ]

    return jsonify({"boxes": payload, "total_boxes": len(payload)})
