#!/usr/bin/env python3
"""
Item management routes for FINDR system.
"""

from flask import Blueprint, request, jsonify
from database import (
    create_item, get_item_by_id, get_all_items, get_items_by_status,
    get_items_by_finder, update_item_status, search_items_by_text
)
import logging
import json

items_bp = Blueprint('items', __name__)
logger = logging.getLogger(__name__)

@items_bp.route('/', methods=['GET'])
def get_items():
    """Get all items with optional filtering."""
    try:
        status = request.args.get('status')
        finder_id = request.args.get('finder_id')
        
        if status:
            items = get_items_by_status(status)
        elif finder_id:
            try:
                finder_id = int(finder_id)
                items = get_items_by_finder(finder_id)
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid finder_id format'
                }), 400
        else:
            items = get_all_items()
        
        # Convert to list of dicts and parse embeddings
        item_list = []
        for item in items:
            item_dict = dict(item)
            
            # Parse JSON embeddings if they exist
            if item_dict.get('image_embedding'):
                try:
                    item_dict['image_embedding'] = json.loads(item_dict['image_embedding'])
                except:
                    item_dict['image_embedding'] = None
            
            if item_dict.get('description_embedding'):
                try:
                    item_dict['description_embedding'] = json.loads(item_dict['description_embedding'])
                except:
                    item_dict['description_embedding'] = None
            
            item_list.append(item_dict)
        
        return jsonify({
            'status': 'success',
            'data': item_list,
            'count': len(item_list)
        })
    
    except Exception as e:
        logger.error(f"Error getting items: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get items',
            'error': str(e)
        }), 500

@items_bp.route('/', methods=['POST'])
def create_new_item():
    """Create a new item."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        description = data.get('description')
        if not description:
            return jsonify({
                'status': 'error',
                'message': 'Description is required'
            }), 400
        
        image_url = data.get('image_url')
        image_embedding = data.get('image_embedding')
        description_embedding = data.get('description_embedding')
        status = data.get('status', 'available')
        finder_user_id = data.get('finder_user_id')
        finder_img_url = data.get('finder_img_url')
        
        item_id = create_item(
            description=description,
            finder_user_id=finder_user_id,
            image_url=image_url,
            image_embedding=image_embedding,
            description_embedding=description_embedding,
            finder_img_url=finder_img_url,
            status=status
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Item created successfully',
            'item_id': item_id
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to create item',
            'error': str(e)
        }), 500

@items_bp.route('/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get item by ID."""
    try:
        item = get_item_by_id(item_id)
        
        if item:
            item_dict = dict(item)
            
            # Parse JSON embeddings if they exist
            if item_dict.get('image_embedding'):
                try:
                    item_dict['image_embedding'] = json.loads(item_dict['image_embedding'])
                except:
                    item_dict['image_embedding'] = None
            
            if item_dict.get('description_embedding'):
                try:
                    item_dict['description_embedding'] = json.loads(item_dict['description_embedding'])
                except:
                    item_dict['description_embedding'] = None
            
            return jsonify({
                'status': 'success',
                'data': item_dict
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Item not found'
            }), 404
    
    except Exception as e:
        logger.error(f"Error getting item {item_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get item',
            'error': str(e)
        }), 500

@items_bp.route('/<int:item_id>/status', methods=['PUT'])
def update_item_status_endpoint(item_id):
    """Update item status."""
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
        
        success = update_item_status(item_id, new_status)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Item status updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Item not found or update failed'
            }), 404
    
    except Exception as e:
        logger.error(f"Error updating item {item_id} status: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update item status',
            'error': str(e)
        }), 500

@items_bp.route('/search', methods=['GET'])
def search_items():
    """Search items by description text."""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Search query (q) parameter is required'
            }), 400
        
        items = search_items_by_text(query)
        
        # Convert to list of dicts and parse embeddings
        item_list = []
        for item in items:
            item_dict = dict(item)
            
            # Parse JSON embeddings if they exist
            if item_dict.get('image_embedding'):
                try:
                    item_dict['image_embedding'] = json.loads(item_dict['image_embedding'])
                except:
                    item_dict['image_embedding'] = None
            
            if item_dict.get('description_embedding'):
                try:
                    item_dict['description_embedding'] = json.loads(item_dict['description_embedding'])
                except:
                    item_dict['description_embedding'] = None
            
            item_list.append(item_dict)
        
        return jsonify({
            'status': 'success',
            'data': item_list,
            'count': len(item_list),
            'query': query
        })
    
    except Exception as e:
        logger.error(f"Error searching items: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to search items',
            'error': str(e)
        }), 500

@items_bp.route('/available', methods=['GET'])
def get_available_items():
    """Get all available items."""
    try:
        items = get_items_by_status('available')
        
        # Convert to list of dicts and parse embeddings
        item_list = []
        for item in items:
            item_dict = dict(item)
            
            # Parse JSON embeddings if they exist
            if item_dict.get('image_embedding'):
                try:
                    item_dict['image_embedding'] = json.loads(item_dict['image_embedding'])
                except:
                    item_dict['image_embedding'] = None
            
            if item_dict.get('description_embedding'):
                try:
                    item_dict['description_embedding'] = json.loads(item_dict['description_embedding'])
                except:
                    item_dict['description_embedding'] = None
            
            item_list.append(item_dict)
        
        return jsonify({
            'status': 'success',
            'data': item_list,
            'count': len(item_list)
        })
    
    except Exception as e:
        logger.error(f"Error getting available items: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get available items',
            'error': str(e)
        }), 500

@items_bp.route('/stats', methods=['GET'])
def get_items_stats():
    """Get item statistics."""
    try:
        all_items = get_all_items()
        available_items = get_items_by_status('available')
        claimed_items = get_items_by_status('claimed')
        
        # Count by status
        status_counts = {}
        for item in all_items:
            status = item['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_items': len(all_items),
                'available_items': len(available_items),
                'claimed_items': len(claimed_items),
                'status_breakdown': status_counts
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting item stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get item statistics',
            'error': str(e)
        }), 500