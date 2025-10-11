from datetime import datetime
from flask import Blueprint, jsonify, request

from database import add_case, get_case, get_all_case, update_case, delete_case, update_box

case_bp = Blueprint("case", __name__)


def _parse_case_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@case_bp.route('/case/add', methods=['POST'])
def add_case_endpoint():
    data = request.get_json() or {}

    box_id = data.get("box_id")
    receiver_id = data.get("receiver_id")
    receiver_image_url = data.get("receiver_image_url")
    item_id = data.get("item_id")
    status = data.get("status", "available")
    case_close_at = data.get("case_close_at")

    if box_id is None or receiver_id is None or item_id is None:
        return jsonify({"error": "box_id, receiver_id and item_id are required"}), 400

    try:
        new_case_id = add_case(
            box_id=int(box_id),
            receiver_id=int(receiver_id) if receiver_id is not None else None,
            receiver_image_url=receiver_image_url,
            item_id=int(item_id),
            status=status,
            case_close_at=case_close_at,
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify({
        "message": "Case created successfully",
        "case_id": new_case_id
    }), 201


@case_bp.route('/case/update', methods=['PUT'])
def update_case_endpoint():
    case_id_value = request.args.get("case_id")
    case_id = _parse_case_id(case_id_value)
    if case_id is None:
        return jsonify({"error": "Valid case_id query parameter is required"}), 400

    data = request.get_json() or {}
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        rows_updated = update_case(
            found_id=case_id,
            status=data.get("status"),
            receiver_id=data.get("receiver_id"),
            receiver_image_url=data.get("receiver_image_url"),
            item_id=data.get("item_id"),
            case_close_at=data.get("case_close_at"),
            box_id=data.get("box_id"),
        )
    except Exception as exc:
        return jsonify({"error": f"Failed to update case {case_id}: {exc}"}), 500

    if rows_updated == 0:
        return jsonify({"error": f"No case found with id {case_id}"}), 404

    return jsonify({
        "message": "Case updated successfully",
        "case_id": case_id
    }), 200


@case_bp.route('/case/<int:case_id>', methods=['GET'])
def get_case_endpoint(case_id: int):
    case = get_case(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404

    return jsonify(dict(case)), 200


@case_bp.route('/case', methods=['GET'])
def list_cases():
    cases = get_all_case()
    return jsonify({
        "cases": [dict(row) for row in cases],
        "total_cases": len(cases)
    }), 200


@case_bp.route('/case/delete/<int:case_id>', methods=['DELETE'])
def delete_case_endpoint(case_id: int):
    deleted = delete_case(case_id)
    if deleted == 0:
        return jsonify({"error": "Case not found"}), 404
    return jsonify({"message": "Case deleted successfully", "case_id": case_id}), 200


@case_bp.route('/case/deposit-complete', methods=['POST'])
def deposit_complete():
    data = request.get_json() or {}
    box_id = _parse_case_id(data.get("box_id"))
    case_id = _parse_case_id(data.get("found_id"))

    if box_id is None or case_id is None:
        return jsonify({"error": "box_id and found_id are required"}), 400

    try:
        update_box(box_id, status=False, door_status=False, load=1)
        update_case(found_id=case_id, status="available_to_claim")
    except Exception as exc:
        return jsonify({"error": f"Failed to complete deposit: {exc}"}), 500

    return jsonify({
        "message": "Deposit completed successfully",
        "box_id": box_id,
        "case_id": case_id,
        "box_status": False,
        "case_status": "available_to_claim"
    }), 200


@case_bp.route('/case/pickup-complete', methods=['POST'])
def pickup_complete():
    data = request.get_json() or {}
    case_id = _parse_case_id(data.get("found_id"))
    box_id = _parse_case_id(data.get("box_id"))

    if case_id is None or box_id is None:
        return jsonify({"error": "found_id and box_id are required"}), 400

    try:
        case_updated = update_case(found_id=case_id, status="retrieved", case_close_at=datetime.now().isoformat())
        box_updated = update_box(box_id, status=True, door_status=False, load=0)
    except Exception as exc:
        return jsonify({"error": f"Failed to complete pickup: {exc}"}), 500

    if case_updated == 0 or box_updated == 0:
        return jsonify({"error": "Case or Box not found"}), 404

    return jsonify({
        "message": "Pickup completed successfully",
        "case_id": case_id,
        "box_id": box_id,
        "case_status": "retrieved",
        "box_status": True
    }), 200
