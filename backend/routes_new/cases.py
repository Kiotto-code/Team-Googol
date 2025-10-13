#!/usr/bin/env python3
"""
Case management routes for FINDR system.
"""

from flask import Blueprint, request, jsonify
from database_new import (
    create_case, get_case_by_id, get_all_cases, get_cases_by_status,
    get_cases_by_box, update_case, claim_case
)
from datetime import datetime
import logging

cases_bp = Blueprint('cases', __name__)
logger = logging.getLogger(__name__)

@cases_bp.route('/', methods=['GET'])
def get_cases():
    """Get all cases with optional filtering."""
    try:
        status = request.args.get('status')
        box_id = request.args.get('box_id')
        
        if status:
            cases = get_cases_by_status(status)
        elif box_id:
            try:
                box_id = int(box_id)
                cases = get_cases_by_box(box_id)
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid box_id format'
                }), 400
        else:
            cases = get_all_cases()
        
        # Convert to list of dicts
        case_list = [dict(case) for case in cases]
        
        return jsonify({
            'status': 'success',
            'data': case_list,
            'count': len(case_list)
        })
    
    except Exception as e:
        logger.error(f"Error getting cases: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get cases',
            'error': str(e)
        }), 500

@cases_bp.route('/', methods=['POST'])
def create_new_case():
    """Create a new case."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        box_id = data.get('box_id')
        if not box_id:
            return jsonify({
                'status': 'error',
                'message': 'Box ID is required'
            }), 400
        
        reciver_id = data.get('reciver_id')
        item_id = data.get('item_id')
        reciver_image_url = data.get('reciver_image_url')
        status = data.get('status', 'available')
        case_close_at = data.get('case_close_at')
        
        # Parse case_close_at if provided
        if case_close_at:
            try:
                case_close_at = datetime.fromisoformat(case_close_at).isoformat()
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid case_close_at format. Use ISO format.'
                }), 400
        
        found_id = create_case(
            box_id=box_id,
            reciver_id=reciver_id,
            item_id=item_id,
            reciver_image_url=reciver_image_url,
            status=status,
            case_close_at=case_close_at
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Case created successfully',
            'found_id': found_id
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating case: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to create case',
            'error': str(e)
        }), 500

@cases_bp.route('/<int:found_id>', methods=['GET'])
def get_case(found_id):
    """Get case by ID."""
    try:
        case = get_case_by_id(found_id)
        
        if case:
            return jsonify({
                'status': 'success',
                'data': dict(case)
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Case not found'
            }), 404
    
    except Exception as e:
        logger.error(f"Error getting case {found_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get case',
            'error': str(e)
        }), 500

@cases_bp.route('/<int:found_id>', methods=['PUT'])
def update_case_endpoint(found_id):
    """Update case details."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Extract update fields
        box_id = data.get('box_id')
        reciver_id = data.get('reciver_id')
        item_id = data.get('item_id')
        reciver_image_url = data.get('reciver_image_url')
        status = data.get('status')
        case_close_at = data.get('case_close_at')
        
        # Parse case_close_at if provided
        if case_close_at:
            try:
                case_close_at = datetime.fromisoformat(case_close_at).isoformat()
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid case_close_at format. Use ISO format.'
                }), 400
        
        success = update_case(
            found_id=found_id,
            box_id=box_id,
            reciver_id=reciver_id,
            item_id=item_id,
            reciver_image_url=reciver_image_url,
            status=status,
            case_close_at=case_close_at
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Case updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Case not found or update failed'
            }), 404
    
    except Exception as e:
        logger.error(f"Error updating case {found_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update case',
            'error': str(e)
        }), 500

@cases_bp.route('/<int:found_id>/claim', methods=['POST'])
def claim_case_endpoint(found_id):
    """Claim a case."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        reciver_id = data.get('reciver_id')
        if not reciver_id:
            return jsonify({
                'status': 'error',
                'message': 'Receiver ID is required'
            }), 400
        
        reciver_image_url = data.get('reciver_image_url')
        
        success, message = claim_case(found_id, reciver_id, reciver_image_url)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
    
    except Exception as e:
        logger.error(f"Error claiming case {found_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to claim case',
            'error': str(e)
        }), 500

@cases_bp.route('/<int:found_id>/status', methods=['PUT'])
def update_case_status(found_id):
    """Update case status only."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        new_status = data.get('status')
        if not new_status:
            return jsonify({
                'status': 'error',
                'message': 'Status is required'
            }), 400
        
        success = update_case(found_id=found_id, status=new_status)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Case status updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Case not found or update failed'
            }), 404
    
    except Exception as e:
        logger.error(f"Error updating case {found_id} status: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update case status',
            'error': str(e)
        }), 500

@cases_bp.route('/<int:found_id>/close', methods=['POST'])
def close_case(found_id):
    """Close a case."""
    try:
        case_close_at = datetime.now().isoformat()
        
        success = update_case(
            found_id=found_id,
            status='closed',
            case_close_at=case_close_at
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Case closed successfully',
                'case_close_at': case_close_at
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Case not found or close failed'
            }), 404
    
    except Exception as e:
        logger.error(f"Error closing case {found_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to close case',
            'error': str(e)
        }), 500

@cases_bp.route('/available', methods=['GET'])
def get_available_cases():
    """Get all available cases."""
    try:
        cases = get_cases_by_status('available')
        
        # Convert to list of dicts
        case_list = [dict(case) for case in cases]
        
        return jsonify({
            'status': 'success',
            'data': case_list,
            'count': len(case_list)
        })
    
    except Exception as e:
        logger.error(f"Error getting available cases: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get available cases',
            'error': str(e)
        }), 500

@cases_bp.route('/stats', methods=['GET'])
def get_cases_stats():
    """Get case statistics."""
    try:
        all_cases = get_all_cases()
        available_cases = get_cases_by_status('available')
        claimed_cases = get_cases_by_status('claimed')
        closed_cases = get_cases_by_status('closed')
        
        # Count by status
        status_counts = {}
        for case in all_cases:
            status = case['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_cases': len(all_cases),
                'available_cases': len(available_cases),
                'claimed_cases': len(claimed_cases),
                'closed_cases': len(closed_cases),
                'status_breakdown': status_counts
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting case stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get case statistics',
            'error': str(e)
        }), 500