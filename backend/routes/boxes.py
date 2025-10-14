#!/usr/bin/env python3
"""
Box management routes for FINDR system.
"""

from flask import Blueprint, request, jsonify
from database import (
    create_box, get_box_by_id, get_all_boxes, get_boxes_by_status,
    update_box, get_cases_by_box
)
import logging

boxes_bp = Blueprint('boxes', __name__)
logger = logging.getLogger(__name__)

@boxes_bp.route('/', methods=['GET'])
def get_boxes():
    """Get all boxes with optional filtering."""
    try:
        status = request.args.get('status')
        
        if status is not None:
            # Convert string to boolean
            status_bool = status.lower() in ('true', '1', 'yes', 'on')
            boxes = get_boxes_by_status(status_bool)
        else:
            boxes = get_all_boxes()
        
        # Convert to list of dicts
        box_list = [dict(box) for box in boxes]
        
        return jsonify({
            'status': 'success',
            'data': box_list,
            'count': len(box_list)
        })
    
    except Exception as e:
        logger.error(f"Error getting boxes: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get boxes',
            'error': str(e)
        }), 500

@boxes_bp.route('/', methods=['POST'])
def create_new_box():
    """Create a new box."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        location = data.get('location')
        if not location:
            return jsonify({
                'status': 'error',
                'message': 'Location is required'
            }), 400
        
        status = data.get('status', True)
        door_status = data.get('door_status', False)
        load = data.get('load', 0)
        
        box_id = create_box(
            location=location,
            status=status,
            door_status=door_status,
            load=load
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Box created successfully',
            'box_id': box_id
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating box: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to create box',
            'error': str(e)
        }), 500

@boxes_bp.route('/<int:box_id>', methods=['GET'])
def get_box(box_id):
    """Get box by ID."""
    try:
        box = get_box_by_id(box_id)
        
        if box:
            return jsonify({
                'status': 'success',
                'data': dict(box)
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Box not found'
            }), 404
    
    except Exception as e:
        logger.error(f"Error getting box {box_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get box',
            'error': str(e)
        }), 500

@boxes_bp.route('/<int:box_id>', methods=['PUT'])
def update_box_endpoint(box_id):
    """Update box details."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Extract update fields
        status = data.get('status')
        location = data.get('location')
        load = data.get('load')
        door_status = data.get('door_status')
        
        success = update_box(
            box_id=box_id,
            status=status,
            location=location,
            load=load,
            door_status=door_status
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Box updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Box not found or update failed'
            }), 404
    
    except Exception as e:
        logger.error(f"Error updating box {box_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update box',
            'error': str(e)
        }), 500

@boxes_bp.route('/<int:box_id>/cases', methods=['GET'])
def get_box_cases(box_id):
    """Get all cases for a specific box."""
    try:
        # Check if box exists
        box = get_box_by_id(box_id)
        if not box:
            return jsonify({
                'status': 'error',
                'message': 'Box not found'
            }), 404
        
        cases = get_cases_by_box(box_id)
        
        # Convert to list of dicts
        case_list = [dict(case) for case in cases]
        
        return jsonify({
            'status': 'success',
            'data': case_list,
            'count': len(case_list),
            'box_id': box_id
        })
    
    except Exception as e:
        logger.error(f"Error getting cases for box {box_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get box cases',
            'error': str(e)
        }), 500

@boxes_bp.route('/<int:box_id>/status', methods=['PUT'])
def update_box_status(box_id):
    """Update box status only."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        new_status = data.get('status')
        if new_status is None:
            return jsonify({
                'status': 'error',
                'message': 'Status is required'
            }), 400
        
        success = update_box(box_id=box_id, status=new_status)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Box status updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Box not found or update failed'
            }), 404
    
    except Exception as e:
        logger.error(f"Error updating box {box_id} status: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update box status',
            'error': str(e)
        }), 500

@boxes_bp.route('/<int:box_id>/door', methods=['PUT'])
def update_box_door_status(box_id):
    """Update box door status only."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        door_status = data.get('door_status')
        if door_status is None:
            return jsonify({
                'status': 'error',
                'message': 'Door status is required'
            }), 400
        
        success = update_box(box_id=box_id, door_status=door_status)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Box door status updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Box not found or update failed'
            }), 404
    
    except Exception as e:
        logger.error(f"Error updating box {box_id} door status: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update box door status',
            'error': str(e)
        }), 500

@boxes_bp.route('/active', methods=['GET'])
def get_active_boxes():
    """Get all active boxes."""
    try:
        boxes = get_boxes_by_status(True)
        
        # Convert to list of dicts
        box_list = [dict(box) for box in boxes]
        
        return jsonify({
            'status': 'success',
            'data': box_list,
            'count': len(box_list)
        })
    
    except Exception as e:
        logger.error(f"Error getting active boxes: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get active boxes',
            'error': str(e)
        }), 500

@boxes_bp.route('/stats', methods=['GET'])
def get_boxes_stats():
    """Get box statistics."""
    try:
        all_boxes = get_all_boxes()
        active_boxes = get_boxes_by_status(True)
        inactive_boxes = get_boxes_by_status(False)
        
        # Calculate load statistics
        total_load = sum(box['load'] for box in all_boxes)
        avg_load = total_load / len(all_boxes) if all_boxes else 0
        
        # Count doors open/closed
        doors_open = sum(1 for box in all_boxes if box['door_status'])
        doors_closed = len(all_boxes) - doors_open
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_boxes': len(all_boxes),
                'active_boxes': len(active_boxes),
                'inactive_boxes': len(inactive_boxes),
                'total_load': total_load,
                'average_load': round(avg_load, 2),
                'doors_open': doors_open,
                'doors_closed': doors_closed
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting box stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get box statistics',
            'error': str(e)
        }), 500