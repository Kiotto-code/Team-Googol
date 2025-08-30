"""
Box status utilities and validation functions.
"""

# Valid box statuses (logical state) - Simplified for 1-item boxes
VALID_BOX_STATUSES = {
    "available",      # Ready to receive 1 item
    "full",          # Has 1 item (at capacity)
    "collect_request", # Full and requesting collection
    "maintenance",    # Under maintenance
    "offline"        # Not operational
}

# Valid door statuses (physical state) - Simplified
VALID_DOOR_STATUSES = {
    "closed",        # Door is closed and locked
    "open"           # Door is open
}

def validate_box_status(status):
    """Validate if box status is valid."""
    return status in VALID_BOX_STATUSES

def validate_door_status(door_status):
    """Validate if door status is valid."""
    return door_status in VALID_DOOR_STATUSES

def get_next_status_after_item_added(current_status, current_load, capacity):
    """Determine next status after an item is added."""
    if current_load >= 1:  # For 1-item boxes, full when load = 1
        return "full"
    else:
        return "available"

def should_request_collection(status, current_load, capacity):
    """Determine if box should request collection."""
    return current_load >= 1  # For 1-item boxes, request collection when 1 item is stored

def get_recommended_door_action(status, door_status):
    """Get recommended door action based on box status."""
    if status == "collect_request" and door_status == "closed":
        return "open"  # Open door for collection
    elif status == "available" and door_status == "open":
        return "close"  # Close door when available
    return None  # No action needed

def format_box_info(box_data):
    """Format box information for display."""
    return {
        "box_id": box_data['id'],
        "status": box_data['status'],
        "door_status": box_data['door_status'],
        "capacity": box_data['capacity'],
        "current_load": box_data['current_load'],
        "last_updated": box_data['last_updated'],
        "is_full": box_data['current_load'] >= 1,  # Full when 1 item
        "needs_collection": box_data['status'] == "collect_request",
        "door_should_be_open": box_data['status'] == "collect_request",
        "status_description": get_status_description(box_data['status']),
        "door_description": get_door_description(box_data['door_status'])
    }

def get_status_description(status):
    """Get human-readable description of box status."""
    descriptions = {
        "available": "Ready to receive 1 item",
        "full": "Contains 1 item (full)",
        "collect_request": "Full - requesting collection",
        "maintenance": "Under maintenance",
        "offline": "Not operational"
    }
    return descriptions.get(status, "Unknown status")

def get_door_description(door_status):
    """Get human-readable description of door status."""
    descriptions = {
        "closed": "Door is closed",
        "open": "Door is open"
    }
    return descriptions.get(door_status, "Unknown door status")
