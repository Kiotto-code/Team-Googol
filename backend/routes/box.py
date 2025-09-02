import os
from flask import Blueprint, request, jsonify
from database import (
    add_box, update_box_status, get_box_status, 
    get_all_boxes, get_collected_items
)

box_bp = Blueprint('box', __name__)

@box_bp.route('/box/register', methods=['POST'])
def register_box():
    """Register a new box in the system."""
    data = request.get_json()
    if not data or 'box_id' not in data:
        return jsonify({"error": "box_id is required"}), 400
    
    box_id = data['box_id']
    capacity = data.get('capacity', 1)  # Default capacity of 1 item per box
    status = data.get('status', 'available')
    
    try:
        add_box(box_id, capacity, status)
        return jsonify({
            "message": "Box registered successfully",
            "box_id": box_id,
            "capacity": capacity,
            "status": status
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to register box: {str(e)}"}), 500

@box_bp.route('/box/<box_id>/status', methods=['GET'])
def get_box_info(box_id):
    """Get the current status and information of a specific box."""
    try:
        box_info = get_box_status(box_id)
        if not box_info:
            return jsonify({"error": "Box not found"}), 404
        
        return jsonify({
            "box_id": box_info['id'],
            "status": box_info['status'],
            "door_status": box_info['door_status'],
            "capacity": box_info['capacity'],
            "current_load": box_info['current_load'],
            "last_updated": box_info['last_updated'],
            "is_full": box_info['current_load'] >= box_info['capacity'],
            "should_open": box_info['status'] == 'collect_request',
            "door_open": box_info['door_status'] == 'open'
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get box status: {str(e)}"}), 500

@box_bp.route('/box/<box_id>/status', methods=['POST'])
def update_box_info(box_id):
    """Update the status of a specific box."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    status = data.get('status')
    door_status = data.get('door_status')
    current_load = data.get('current_load')
    
    if status is None and door_status is None and current_load is None:
        return jsonify({"error": "At least one of status, door_status, or current_load must be provided"}), 400
    
    try:
        success = update_box_status(box_id, status, door_status, current_load)
        if not success:
            return jsonify({"error": "Box not found"}), 404
        
        # Get updated box info
        updated_box = get_box_status(box_id)
        return jsonify({
            "message": "Box status updated successfully",
            "box_id": box_id,
            "status": updated_box['status'],
            "door_status": updated_box['door_status'],
            "current_load": updated_box['current_load'],
            "last_updated": updated_box['last_updated']
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to update box status: {str(e)}"}), 500

@box_bp.route('/box/<box_id>/door/open', methods=['POST'])
def open_door(box_id):
    """Open the box door for item collection."""
    try:
        # Check if box exists
        box_info = get_box_status(box_id)
        if not box_info:
            return jsonify({"error": "Box not found"}), 404
        
        # Open the door
        success = update_box_status(box_id, door_status='open')
        if not success:
            return jsonify({"error": "Failed to open door"}), 500
        
        return jsonify({
            "message": "Door opened successfully",
            "box_id": box_id,
            "door_status": "open",
            "instruction": "Box door is now open for item collection"
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to open door: {str(e)}"}), 500

@box_bp.route('/box/<box_id>/door/close', methods=['POST'])
def close_door(box_id):
    """Close the box door after collection."""
    try:
        # Check if box exists
        box_info = get_box_status(box_id)
        if not box_info:
            return jsonify({"error": "Box not found"}), 404
        
        # Close the door
        success = update_box_status(box_id, door_status='closed')
        if not success:
            return jsonify({"error": "Failed to close door"}), 500
        
        return jsonify({
            "message": "Door closed successfully",
            "box_id": box_id,
            "door_status": "closed"
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to close door: {str(e)}"}), 500

@box_bp.route('/box/<box_id>/request_collection', methods=['POST'])
def request_collection(box_id):
    """Request collection for a box (signal it to open for item retrieval)."""
    try:
        # Check if box exists
        box_info = get_box_status(box_id)
        if not box_info:
            return jsonify({"error": "Box not found"}), 404
        
        # Update status to request collection and open door
        success = update_box_status(box_id, status='collect_request', door_status='open')
        if not success:
            return jsonify({"error": "Failed to update box status"}), 500
        
        return jsonify({
            "message": "Collection requested successfully",
            "box_id": box_id,
            "status": "collect_request",
            "door_status": "open",
            "instruction": "Box door is now open for item collection"
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to request collection: {str(e)}"}), 500

@box_bp.route('/box/<box_id>/collection_complete', methods=['POST'])
def collection_complete(box_id):
    """Mark collection as complete and return box to available status."""
    try:
        # Check if box exists
        box_info = get_box_status(box_id)
        if not box_info:
            return jsonify({"error": "Box not found"}), 404
        
        # Reset box status, load, and close door
        success = update_box_status(box_id, status='available', door_status='closed', current_load=0)
        if not success:
            return jsonify({"error": "Failed to update box status"}), 500
        
        return jsonify({
            "message": "Collection completed successfully",
            "box_id": box_id,
            "status": "available",
            "door_status": "closed",
            "current_load": 0
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to complete collection: {str(e)}"}), 500

@box_bp.route('/boxes', methods=['GET'])
def get_boxes():
    """Get information about all boxes in the system."""
    try:
        boxes = get_all_boxes()
        boxes_data = []
        
        for box in boxes:
            boxes_data.append({
                "box_id": box['id'],
                "status": box['status'],
                "door_status": box['door_status'],
                "capacity": box['capacity'],
                "current_load": box['current_load'],
                "last_updated": box['last_updated'],
                "is_full": box['current_load'] >= box['capacity'],
                "should_open": box['status'] == 'collect_request',
                "door_open": box['door_status'] == 'open'
            })
        
        return jsonify({
            "boxes": boxes_data,
            "total_boxes": len(boxes_data)
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get boxes: {str(e)}"}), 500

@box_bp.route('/box/<box_id>/items', methods=['GET'])
def get_box_items(box_id):
    """Get all items currently associated with a specific box."""
    try:
        # Get all collected items for this box
        all_collected = get_collected_items()
        box_items = [item for item in all_collected if item['box_id'] == box_id]
        
        return jsonify({
            "box_id": box_id,
            "items": [
                {
                    "id": item['id'],
                    "filename": item['filename'],
                    "timestamp": item['imgtaken_timestamp'],
                    "uploaded_at": item['uploaded_at']
                }
                for item in box_items
            ],
            "item_count": len(box_items)
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get box items: {str(e)}"}), 500
