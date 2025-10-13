#!/usr/bin/env python3
"""
User management routes for FINDR system.
"""

from flask import Blueprint, request, jsonify
from database_new import (
    get_user_by_id, get_all_users, get_user_dashboard_data,
    update_user_stats, get_user_by_email, get_user_by_student_id
)
import logging

users_bp = Blueprint('users', __name__)
logger = logging.getLogger(__name__)

@users_bp.route('/', methods=['GET'])
def get_users():
    """Get all users."""
    try:
        users = get_all_users()
        
        # Convert to list of dicts and remove sensitive data
        user_list = []
        for user in users:
            user_dict = dict(user)
            user_dict.pop('password', None)  # Remove password from response
            user_list.append(user_dict)
        
        return jsonify({
            'status': 'success',
            'data': user_list,
            'count': len(user_list)
        })
    
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get users',
            'error': str(e)
        }), 500

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID."""
    try:
        user = get_user_by_id(user_id)
        
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
        logger.error(f"Error getting user {user_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get user',
            'error': str(e)
        }), 500

@users_bp.route('/<int:user_id>/dashboard', methods=['GET'])
def get_user_dashboard(user_id):
    """Get dashboard data for a user."""
    try:
        dashboard_data = get_user_dashboard_data(user_id)
        
        if dashboard_data:
            # Remove password from user data
            dashboard_data['user'].pop('password', None)
            
            return jsonify({
                'status': 'success',
                'data': dashboard_data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
    
    except Exception as e:
        logger.error(f"Error getting dashboard for user {user_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get dashboard data',
            'error': str(e)
        }), 500

@users_bp.route('/<int:user_id>/stats', methods=['PUT'])
def update_user_statistics(user_id):
    """Update user statistics."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        items_found_increment = data.get('items_found_increment', 0)
        items_find_increment = data.get('items_find_increment', 0)
        
        success = update_user_stats(
            user_id, 
            items_found_increment=items_found_increment,
            items_find_increment=items_find_increment
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'User statistics updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'User not found or update failed'
            }), 404
    
    except Exception as e:
        logger.error(f"Error updating stats for user {user_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update user statistics',
            'error': str(e)
        }), 500

@users_bp.route('/search', methods=['GET'])
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

@users_bp.route('/stats', methods=['GET'])
def get_users_stats():
    """Get user statistics summary."""
    try:
        users = get_all_users()
        
        total_users = len(users)
        total_items_found = sum(user['items_found'] for user in users)
        total_items_claimed = sum(user['items_find'] for user in users)
        
        # Find top contributors
        top_finders = sorted(users, key=lambda x: x['items_found'], reverse=True)[:5]
        top_claimers = sorted(users, key=lambda x: x['items_find'], reverse=True)[:5]
        
        # Remove passwords from top lists
        for user in top_finders + top_claimers:
            user.pop('password', None)
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_users': total_users,
                'total_items_found': total_items_found,
                'total_items_claimed': total_items_claimed,
                'top_finders': [dict(user) for user in top_finders],
                'top_claimers': [dict(user) for user in top_claimers]
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get user statistics',
            'error': str(e)
        }), 500