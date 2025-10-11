from flask import Blueprint, request, jsonify
from database import (
    add_box, update_box, get_box_status,
    get_all_boxes, get_collected_items
)


def _to_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "open", "available"}
    return bool(value)

box_bp = Blueprint('box', __name__)


@box_bp.route('/box/register', methods=['POST'])
def register_box():
    """Register a new box in the system."""
    data = request.get_json()

    # Validate input
    if not data or not data.get("location"):
        return jsonify({"error": "location is required"}), 400

    location = str(data["location"]).strip()
    status = _to_bool(data.get("status"), True)         # default available
    door_status = _to_bool(data.get("door_status"), False)  # default closed
    load_value = data.get("load", 0)
    try:
        load = int(load_value)
    except (TypeError, ValueError):
        return jsonify({"error": "load must be an integer"}), 400

    try:
        new_box_id = add_box(location, status, door_status, load)
        return jsonify({
            "message": "Box registered successfully",
            "box_id": new_box_id,
            "location": location,
            "status": status,
            "door_status": door_status,
            "load": load
        }), 201  # 201 = created
    except Exception as e:
        return jsonify({"error": f"Failed to register box: {str(e)}"}), 500


@box_bp.route('/box/status', methods=['GET'])
def get_box_info():
    """Get the current status and information of a specific box."""
    try:
        box_id_value = request.args.get("box_id")
        if not box_id_value:
            return jsonify({"error": "box_id query parameter is required"}), 400

        try:
            box_id = int(box_id_value)
        except (TypeError, ValueError):
            return jsonify({"error": "box_id must be an integer"}), 400

        box_info = get_box_status(box_id)  # should return a dict from DB row

        if not box_info:
            return jsonify({"error": f"Box with id '{box_id}' not found"}), 404

        response = {
            "box_id": box_info["box_id"],             # INTEGER
            "status": bool(box_info["status"]),       # BOOLEAN
            "door_status": bool(box_info["door_status"]), # BOOLEAN
            "location": box_info["location"],         # VARCHAR
            "load": box_info["load"],                 # INTEGER
            "last_accessed": box_info["last_accessed"]# TIMESTAMP
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve box status: {str(e)}"}), 500



@box_bp.route('/box/status', methods=['POST'])
def update_box_info():
    """Update the status or details of a specific box."""
    box_id_value = request.args.get("box_id")
    if not box_id_value:
        return jsonify({"error": "box_id query parameter is required"}), 400

    try:
        box_id_int = int(box_id_value)
    except (TypeError, ValueError):
        return jsonify({"error": "box_id must be an integer"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Extract possible fields to update
    status = data.get("status")
    door_status = data.get("door_status")
    location = data.get("location")
    load_value = data.get("load")
    parsed_load = None
    if load_value is not None:
        try:
            parsed_load = int(load_value)
        except (TypeError, ValueError):
            return jsonify({"error": "load must be an integer"}), 400

    # Validate input
    if all(v is None for v in [status, door_status, location, load]):
        return jsonify({
            "error": "At least one of status, door_status, location, or load must be provided"
        }), 400

    try:
        # Update in DB (this also updates last_accessed automatically)
        parsed_status = None if status is None else _to_bool(status)
        parsed_door_status = None if door_status is None else _to_bool(door_status)

        success = update_box(
            box_id=box_id_int,
            status=parsed_status,
            door_status=parsed_door_status,
            location=location,
            load=parsed_load
        )

        if not success:
            return jsonify({"error": f"Box with id '{box_id}' not found"}), 404

        # Fetch updated row
        updated_box = get_box_status(box_id_int)

        response = {
            "message": "Box updated successfully",
            "box_id": updated_box["box_id"],
            "status": bool(updated_box["status"]),
            "door_status": bool(updated_box["door_status"]),
            "location": updated_box["location"],
            "load": updated_box["load"],
            "last_accessed": updated_box["last_accessed"],
            # Example computed fields
            "is_empty": int(updated_box["load"]) == 0,
            "is_occupied": int(updated_box["load"]) > 0,
            "door_open": bool(updated_box["door_status"])
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update box '{box_id}': {str(e)}"}), 500

@box_bp.route('/box/open', methods=['POST'])
def open_box():
    """Open the door of a specific box."""
    data = request.get_json()
    if not data or not data.get("box_id"):
        return jsonify({"error": "box_id is required"}), 400

    try:
        box_id = int(data["box_id"])
    except (TypeError, ValueError):
        return jsonify({"error": "box_id must be an integer"}), 400

    try:
        success = update_box(box_id=box_id, door_status=True)

        if not success:
            return jsonify({"error": f"Box with id '{box_id}' not found"}), 404

        updated_box = get_box_status(box_id)

        return jsonify({
            "message": "Box opened successfully",
            "box_id": updated_box["box_id"],
            "door_status": bool(updated_box["door_status"]),
            "last_accessed": updated_box["last_accessed"]
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to open box '{box_id}': {str(e)}"}), 500


@box_bp.route('/box/close', methods=['POST'])
def close_box():
    """Close the door of a specific box."""
    data = request.get_json()
    if not data or not data.get("box_id"):
        return jsonify({"error": "box_id is required"}), 400

    try:
        box_id = int(data["box_id"])
    except (TypeError, ValueError):
        return jsonify({"error": "box_id must be an integer"}), 400

    try:
        success = update_box(box_id=box_id, door_status=False)

        if not success:
            return jsonify({"error": f"Box with id '{box_id}' not found"}), 404

        updated_box = get_box_status(box_id)

        return jsonify({
            "message": "Box closed successfully",
            "box_id": updated_box["box_id"],
            "door_status": bool(updated_box["door_status"]),
            "last_accessed": updated_box["last_accessed"]
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to close box '{box_id}': {str(e)}"}), 500
    
@box_bp.route('/box/all', methods=['GET'])
def get_boxes():
    """Get information about all boxes in the system."""
    try:
        boxes = get_all_boxes()  # should return a list of rows/dicts from DB
        boxes_data = []
        
        for box in boxes:
            boxes_data.append({
                "box_id": box["box_id"],                  # INTEGER
                "status": bool(box["status"]),            # BOOLEAN
                "door_status": bool(box["door_status"]),  # BOOLEAN
                "location": box["location"],              # VARCHAR
                "load": box["load"],                      # INTEGER
                "last_accessed": box["last_accessed"],    # TIMESTAMP
            })
        
        return jsonify({
            "boxes": boxes_data,
            "total_boxes": len(boxes_data)
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get boxes: {str(e)}"}), 500
    

# @box_bp.route('/box/<box_id>/door/open', methods=['POST'])
# def open_door(box_id):
#     """Open the box door for item collection."""
#     try:
#         # Check if box exists
#         box_info = get_box_status(box_id)
#         if not box_info:
#             return jsonify({"error": "Box not found"}), 404
        
#         # Open the door
#         success = update_box_status(box_id, door_status='open')
#         if not success:
#             return jsonify({"error": "Failed to open door"}), 500
        
#         return jsonify({
#             "message": "Door opened successfully",
#             "box_id": box_id,
#             "door_status": "open",
#             "instruction": "Box door is now open for item collection"
#         }), 200
#     except Exception as e:
#         return jsonify({"error": f"Failed to open door: {str(e)}"}), 500

# @box_bp.route('/box/<box_id>/door/close', methods=['POST'])
# def close_door(box_id):
#     """Close the box door after collection."""
#     try:
#         # Check if box exists
#         box_info = get_box_status(box_id)
#         if not box_info:
#             return jsonify({"error": "Box not found"}), 404
        
#         # Close the door
#         success = update_box_status(box_id, door_status='closed')
#         if not success:
#             return jsonify({"error": "Failed to close door"}), 500
        
#         return jsonify({
#             "message": "Door closed successfully",
#             "box_id": box_id,
#             "door_status": "closed"
#         }), 200
#     except Exception as e:
#         return jsonify({"error": f"Failed to close door: {str(e)}"}), 500

# @box_bp.route('/box/<box_id>/request_collection', methods=['POST'])
# def request_collection(box_id):
#     """Request collection for a box (signal it to open for item retrieval)."""
#     try:
#         # Check if box exists
#         box_info = get_box_status(box_id)
#         if not box_info:
#             return jsonify({"error": "Box not found"}), 404
        
#         # Update status to request collection and open door
#         success = update_box_status(box_id, status='collect_request', door_status='open')
#         if not success:
#             return jsonify({"error": "Failed to update box status"}), 500
        
#         return jsonify({
#             "message": "Collection requested successfully",
#             "box_id": box_id,
#             "status": "collect_request",
#             "door_status": "open",
#             "instruction": "Box door is now open for item collection"
#         }), 200
#     except Exception as e:
#         return jsonify({"error": f"Failed to request collection: {str(e)}"}), 500

# @box_bp.route('/box/<box_id>/collection_complete', methods=['POST'])
# def collection_complete(box_id):
#     """Mark collection as complete and return box to available status."""
#     try:
#         # Check if box exists
#         box_info = get_box_status(box_id)
#         if not box_info:
#             return jsonify({"error": "Box not found"}), 404
        
#         # Reset box status, load, and close door
#         success = update_box_status(box_id, status='available', door_status='closed', current_load=0)
#         if not success:
#             return jsonify({"error": "Failed to update box status"}), 500
        
#         return jsonify({
#             "message": "Collection completed successfully",
#             "box_id": box_id,
#             "status": "available",
#             "door_status": "closed",
#             "current_load": 0
#         }), 200
#     except Exception as e:
#         return jsonify({"error": f"Failed to complete collection: {str(e)}"}), 500

# @box_bp.route('/box/<box_id>/items', methods=['GET'])
# def get_box_items(box_id):
#     """Get all items currently associated with a specific box."""
#     try:
#         # Get all collected items for this box
#         all_collected = get_collected_items()
#         box_items = [item for item in all_collected if item['box_id'] == box_id]
        
#         return jsonify({
#             "box_id": box_id,
#             "items": [
#                 {
#                     "id": item['id'],
#                     "filename": item['filename'],
#                     "timestamp": item['imgtaken_timestamp'],
#                     "uploaded_at": item['uploaded_at']
#                 }
#                 for item in box_items
#             ],
#             "item_count": len(box_items)
#         }), 200
#     except Exception as e:
#         return jsonify({"error": f"Failed to get box items: {str(e)}"}), 500
