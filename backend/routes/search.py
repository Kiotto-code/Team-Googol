#!/usr/bin/env python3
"""
Search routes for FINDR system.
"""

from flask import Blueprint, request, jsonify
from database import (
    search_items_by_text, get_items_by_status, get_all_items,
    get_user_by_email, get_user_by_student_id
)
import json
import logging

search_bp = Blueprint('search', __name__)
logger = logging.getLogger(__name__)

@search_bp.route('/items', methods=['GET'])
def search_items():
    """Search items by text query."""
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

@search_bp.route('/items/advanced', methods=['POST'])
def advanced_item_search():
    """Advanced item search with multiple criteria."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No search criteria provided'
            }), 400
        
        # Get all items first
        all_items = get_all_items()
        filtered_items = []
        
        # Apply filters
        for item in all_items:
            item_dict = dict(item)
            include_item = True
            
            # Filter by description text
            if data.get('description'):
                if data['description'].lower() not in item_dict['description'].lower():
                    include_item = False
            
            # Filter by status
            if data.get('status'):
                if item_dict['status'] != data['status']:
                    include_item = False
            
            # Filter by finder
            if data.get('finder_user_id'):
                if item_dict['finder_user_id'] != data['finder_user_id']:
                    include_item = False
            
            # Filter by date range
            if data.get('start_date') or data.get('end_date'):
                item_date = item_dict['created_at']
                
                if data.get('start_date'):
                    if item_date < data['start_date']:
                        include_item = False
                
                if data.get('end_date'):
                    if item_date > data['end_date']:
                        include_item = False
            
            if include_item:
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
                
                filtered_items.append(item_dict)
        
        # Sort results
        sort_by = data.get('sort_by', 'created_at')
        sort_order = data.get('sort_order', 'desc')
        
        if sort_by in ['created_at', 'item_id', 'status', 'description']:
            filtered_items.sort(
                key=lambda x: x.get(sort_by, ''),
                reverse=(sort_order.lower() == 'desc')
            )
        
        # Limit results
        limit = data.get('limit')
        if limit and limit > 0:
            filtered_items = filtered_items[:limit]
        
        return jsonify({
            'status': 'success',
            'data': filtered_items,
            'count': len(filtered_items),
            'search_criteria': data
        })
    
    except Exception as e:
        logger.error(f"Error in advanced item search: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to perform advanced search',
            'error': str(e)
        }), 500

@search_bp.route('/users', methods=['GET'])
def search_users():
    """Search users by email or student ID."""
    try:
        email = request.args.get('email')
        student_id = request.args.get('student_id')
        
        if email:
            user = get_user_by_email(email)
        elif student_id:
            try:
                student_id = int(student_id)
                user = get_user_by_student_id(student_id)
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid student ID format'
                }), 400
        else:
            return jsonify({
                'status': 'error',
                'message': 'Email or student_id parameter required'
            }), 400
        
        if user:
            user_dict = dict(user)
            user_dict.pop('password', None)  # Remove password from response
            
            return jsonify({
                'status': 'success',
                'data': user_dict
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
    
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to search users',
            'error': str(e)
        }), 500

@search_bp.route('/items/by-embedding', methods=['POST'])
def search_items_by_embedding():
    """Search items by image or description embedding similarity."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No search data provided'
            }), 400
        
        query_embedding = data.get('embedding')
        search_type = data.get('type', 'image')  # 'image' or 'description'
        similarity_threshold = data.get('threshold', 0.8)
        limit = data.get('limit', 10)
        
        if not query_embedding:
            return jsonify({
                'status': 'error',
                'message': 'Embedding is required'
            }), 400
        
        # Get all available items
        items = get_items_by_status('available')
        similar_items = []
        
        for item in items:
            item_dict = dict(item)
            
            # Get the appropriate embedding
            if search_type == 'image' and item_dict.get('image_embedding'):
                try:
                    stored_embedding = json.loads(item_dict['image_embedding'])
                    similarity = calculate_cosine_similarity(query_embedding, stored_embedding)
                    
                    if similarity >= similarity_threshold:
                        item_dict['similarity_score'] = similarity
                        
                        # Parse embeddings for response
                        item_dict['image_embedding'] = stored_embedding
                        if item_dict.get('description_embedding'):
                            try:
                                item_dict['description_embedding'] = json.loads(item_dict['description_embedding'])
                            except:
                                item_dict['description_embedding'] = None
                        
                        similar_items.append(item_dict)
                except:
                    continue
            
            elif search_type == 'description' and item_dict.get('description_embedding'):
                try:
                    stored_embedding = json.loads(item_dict['description_embedding'])
                    similarity = calculate_cosine_similarity(query_embedding, stored_embedding)
                    
                    if similarity >= similarity_threshold:
                        item_dict['similarity_score'] = similarity
                        
                        # Parse embeddings for response
                        item_dict['description_embedding'] = stored_embedding
                        if item_dict.get('image_embedding'):
                            try:
                                item_dict['image_embedding'] = json.loads(item_dict['image_embedding'])
                            except:
                                item_dict['image_embedding'] = None
                        
                        similar_items.append(item_dict)
                except:
                    continue
        
        # Sort by similarity score (highest first)
        similar_items.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Limit results
        if limit > 0:
            similar_items = similar_items[:limit]
        
        return jsonify({
            'status': 'success',
            'data': similar_items,
            'count': len(similar_items),
            'search_type': search_type,
            'threshold': similarity_threshold
        })
    
    except Exception as e:
        logger.error(f"Error searching by embedding: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to search by embedding',
            'error': str(e)
        }), 500

def calculate_cosine_similarity(embedding1, embedding2):
    """Calculate cosine similarity between two embeddings."""
    try:
        import numpy as np
        
        # Convert to numpy arrays
        a = np.array(embedding1)
        b = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0
        
        similarity = dot_product / (norm_a * norm_b)
        return float(similarity)
    
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0

@search_bp.route('/suggestions', methods=['GET'])
def get_search_suggestions():
    """Get search suggestions based on existing items."""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 5))
        
        if not query:
            return jsonify({
                'status': 'success',
                'data': [],
                'count': 0
            })
        
        # Get all items and extract unique words from descriptions
        items = get_all_items()
        suggestions = set()
        
        for item in items:
            description = item['description'].lower()
            words = description.split()
            
            for word in words:
                # Clean word (remove punctuation)
                clean_word = ''.join(c for c in word if c.isalnum())
                
                if (len(clean_word) > 2 and 
                    clean_word.startswith(query.lower()) and
                    clean_word != query.lower()):
                    suggestions.add(clean_word)
        
        # Convert to list and sort
        suggestion_list = sorted(list(suggestions))[:limit]
        
        return jsonify({
            'status': 'success',
            'data': suggestion_list,
            'count': len(suggestion_list),
            'query': query
        })
    
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get search suggestions',
            'error': str(e)
        }), 500