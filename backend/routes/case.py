from flask import Blueprint, request, jsonify
from database import add_case, update_case, update_box

case_bp = Blueprint("case_bp", __name__)

@case_bp.route('/case/add', methods=['POST'])
def add_case_endpoint():
    try:
        data = request.get_json()
        box_id = data.get("box_id")
        receiver_id = data.get("receiver_id")
        receiver_image_url = data.get("receiver_image_url")
        item_id = data.get("item_id")
        status = data.get("status", "available")
        case_close_at = data.get("case_close_at")

        if not box_id or not receiver_id or not item_id:
            return jsonify({"error": "box_id, receiver_id and item_id are required"}), 400

        new_case_id = add_case(box_id, receiver_id, receiver_image_url, item_id, status, case_close_at)

        return jsonify({
            "message": "Case created successfully",
            "case_id": new_case_id
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@case_bp.route('/case/update', methods=['PUT'])
def update_case_endpoint():
    """Update details of an existing case using query parameter ?case_id."""
    case_id = request.args.get("case_id")

    if not case_id:
        return jsonify({"error": "case_id query parameter is required"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Extract possible fields
    status = data.get("status")
    receiver_id = data.get("receiver_id")
    receiver_image_url = data.get("receiver_image_url")
    item_id = data.get("item_id")
    case_close_at = data.get("case_close_at")

    if all(v is None for v in [status, receiver_id, receiver_image_url, item_id, case_close_at]):
        return jsonify({
            "error": "At least one of status, receiver_id, receiver_image_url, item_id, or case_close_at must be provided"
        }), 400

    try:
        rows_updated = update_case(
            case_id=case_id,
            status=status,
            receiver_id=receiver_id,
            receiver_image_url=receiver_image_url,
            item_id=item_id,
            case_close_at=case_close_at
        )

        if rows_updated == 0:
            return jsonify({"error": f"No case found with id {case_id}"}), 404

        return jsonify({
            "message": "Case updated successfully",
            "case_id": int(case_id),
            "status": status if status is not None else "unchanged",
            "receiver_id": receiver_id if receiver_id is not None else "unchanged",
            "receiver_image_url": receiver_image_url if receiver_image_url is not None else "unchanged",
            "item_id": item_id if item_id is not None else "unchanged",
            "case_close_at": case_close_at if case_close_at is not None else "unchanged"
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update case {case_id}: {str(e)}"}), 500
    
@case_bp.route('/case/deposit-complete', methods=['POST'])
def deposit_complete():
    """Mark a box as full and its related case as available_to_claim after deposit."""
    data = request.get_json()
    if not data or not data.get("box_id") or not data.get("found_id"):
        return jsonify({"error": "box_id and found_id are required"}), 400

    box_id = data["box_id"]
    found_id = data["found_id"]

    try:
        # 1. Update BOXES → mark full (status=False) and load=1
        update_box(
            box_id=box_id,
            status=False, # False = not available
            door_status=False,
            load=1
        )

        # 2. Update CASES → mark status as 'available_to_claim'
        update_case(
            found_id=found_id,
            status="available_to_claim"
        )

        return jsonify({
            "message": "Deposit completed successfully",
            "box_id": box_id,
            "case_id": found_id,
            "box_status": "full",
            "case_status": "available_to_claim"
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to complete deposit: {str(e)}"}), 500
    
@case_bp.route('/case/pickup-complete', methods=['POST'])
def pickup_complete():
    """
    Mark case as retrieved and free up the box.
    Request body must contain: { "found_id": <case_id>, "box_id": <box_id> }
    """
    data = request.get_json()
    found_id = data.get("found_id")
    box_id = data.get("box_id")

    if not found_id or not box_id:
        return jsonify({"error": "found_id and box_id are required"}), 400

    try:
        # 1. Update case status to 'retrieved'
        updated_case = update_case(found_id, status="retrieved")

        # 2. Update box status to 'available'
        updated_box = update_box(box_id, status=True, load=0, door_status=False)

        if updated_case == 0 or updated_box == 0:
            return jsonify({"error": "Case or Box not found"}), 404

        return jsonify({
            "message": "Pickup completed successfully",
            "case_id": found_id,
            "box_id": box_id,
            "case_status": "retrieved",
            "box_status": True
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to complete pickup: {str(e)}"}), 500