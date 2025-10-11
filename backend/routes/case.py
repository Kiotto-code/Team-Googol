from flask import Blueprint, jsonify, request

from database import create_case, delete_case, get_case, update_box, update_case

case_bp = Blueprint("case", __name__)


@case_bp.route("/case/add", methods=["POST"])
def add_case_endpoint():
    data = request.get_json() or {}

    box_id = data.get("box_id")
    item_id = data.get("item_id")
    if box_id is None or item_id is None:
        return jsonify({"error": "box_id and item_id are required"}), 400

    try:
        box_id = int(box_id)
        item_id = int(item_id)
    except (TypeError, ValueError):
        return jsonify({"error": "box_id and item_id must be integers"}), 400

    receiver_id = data.get("receiver_id")
    receiver_image_url = data.get("receiver_image_url")
    status = data.get("status", "available")
    case_close_at = data.get("case_close_at")

    receiver_id_value = None
    if receiver_id is not None:
        try:
            receiver_id_value = int(receiver_id)
        except (TypeError, ValueError):
            return jsonify({"error": "receiver_id must be an integer"}), 400

    try:
        case_id = create_case(
            box_id=box_id,
            reciver_image_url=receiver_image_url,
            reciver_id=receiver_id_value,
            item_id=item_id,
            status=status,
            case_close_at=case_close_at,
        )
        return jsonify({"message": "Case created successfully", "case_id": case_id}), 201
    except Exception as exc:  # pragma: no cover - sqlite safety net
        return jsonify({"error": f"Failed to create case: {exc}"}), 500


@case_bp.route("/case/<int:case_id>", methods=["PUT"])
def update_case_endpoint(case_id: int):
    data = request.get_json() or {}
    if not data:
        return jsonify({"error": "No data provided"}), 400

    box_id = data.get("box_id")
    item_id = data.get("item_id")
    status = data.get("status")
    receiver_id = data.get("receiver_id")
    receiver_image_url = data.get("receiver_image_url")
    case_close_at = data.get("case_close_at")

    if all(value is None for value in (box_id, item_id, status, receiver_id, receiver_image_url, case_close_at)):
        return jsonify({"error": "No updatable fields provided"}), 400

    receiver_id_value = None
    if receiver_id is not None:
        try:
            receiver_id_value = int(receiver_id)
        except (TypeError, ValueError):
            return jsonify({"error": "receiver_id must be an integer"}), 400

    box_id_value = None
    if box_id is not None:
        try:
            box_id_value = int(box_id)
        except (TypeError, ValueError):
            return jsonify({"error": "box_id must be an integer"}), 400

    item_id_value = None
    if item_id is not None:
        try:
            item_id_value = int(item_id)
        except (TypeError, ValueError):
            return jsonify({"error": "item_id must be an integer"}), 400

    updated = update_case(
        case_id,
        box_id=box_id_value,
        item_id=item_id_value,
        status=status,
        reciver_id=receiver_id_value,
        reciver_image_url=receiver_image_url,
        case_close_at=case_close_at,
    )

    if updated == 0:
        return jsonify({"error": f"No case found with id {case_id}"}), 404

    refreshed = get_case(case_id)
    return jsonify(
        {
            "message": "Case updated successfully",
            "case_id": case_id,
            "status": refreshed["status"],
            "box_id": refreshed["box_id"],
            "item_id": refreshed["item_id"],
            "receiver_id": refreshed["reciver_id"],
            "receiver_image_url": refreshed["reciver_image_url"],
            "case_close_at": refreshed["case_close_at"],
        }
    )


@case_bp.route("/case/<int:case_id>", methods=["DELETE"])
def delete_case_endpoint(case_id: int):
    removed = delete_case(case_id)
    if not removed:
        return jsonify({"error": "Case not found"}), 404
    return jsonify({"message": "Case deleted"})


@case_bp.route("/case/deposit-complete", methods=["POST"])
def deposit_complete():
    data = request.get_json() or {}
    box_id = data.get("box_id")
    case_id = data.get("found_id") or data.get("case_id")

    if not box_id or not case_id:
        return jsonify({"error": "box_id and case_id are required"}), 400

    try:
        box_id = int(box_id)
        case_id = int(case_id)
    except (TypeError, ValueError):
        return jsonify({"error": "box_id and case_id must be integers"}), 400

    update_box(box_id, status=False, load=1, door_status=False)
    update_case(case_id, status="available")

    return jsonify(
        {
            "message": "Deposit completed successfully",
            "box_id": box_id,
            "case_id": case_id,
            "box_status": False,
            "case_status": "available",
        }
    )


@case_bp.route("/case/pickup-complete", methods=["POST"])
def pickup_complete():
    data = request.get_json() or {}
    case_id = data.get("found_id") or data.get("case_id")
    box_id = data.get("box_id")

    if not case_id or not box_id:
        return jsonify({"error": "case_id and box_id are required"}), 400

    try:
        case_id = int(case_id)
        box_id = int(box_id)
    except (TypeError, ValueError):
        return jsonify({"error": "case_id and box_id must be integers"}), 400

    case_updated = update_case(case_id, status="retrieved")
    box_updated = update_box(box_id, status=True, load=0, door_status=False)

    if case_updated == 0 or box_updated == 0:
        return jsonify({"error": "Case or Box not found"}), 404

    return jsonify(
        {
            "message": "Pickup completed successfully",
            "case_id": case_id,
            "box_id": box_id,
            "case_status": "retrieved",
            "box_status": True,
        }
    )
