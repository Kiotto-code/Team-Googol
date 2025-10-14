#!/usr/bin/env python3
"""
Authentication routes for FINDR system.
"""

from flask import Blueprint, request, jsonify, session
from database import (
    authenticate_user, create_user, get_user_by_email, 
    get_user_by_rfid, get_user_by_student_id
)
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'status': 'error',
                'message': 'Email and password are required'
            }), 400
        
        # Authenticate user
        user = authenticate_user(email, password)
        
        if user:
            # Store user ID in session
            session['user_id'] = user['user_id']
            session['email'] = user['email']
            
            return jsonify({
                'status': 'success',
                'message': 'Login successful',
                'user': {
                    'user_id': user['user_id'],
                    'name': user['name'],
                    'email': user['email'],
                    'student_id': user['student_id'],
                    'items_found': user['items_found'],
                    'items_find': user['items_find']
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid email or password'
            }), 401
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Login failed',
            'error': str(e)
        }), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        phone_number = data.get('phone_number')
        student_id = data.get('student_id')
        rfid_tag = data.get('rfid_tag')
        
        # Validate required fields
        if not all([name, email, password]):
            return jsonify({
                'status': 'error',
                'message': 'Name, email, and password are required'
            }), 400
        
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            return jsonify({
                'status': 'error',
                'message': 'User with this email already exists'
            }), 409
        
        # Check if student ID already exists
        if student_id:
            existing_student = get_user_by_student_id(student_id)
            if existing_student:
                return jsonify({
                    'status': 'error',
                    'message': 'User with this student ID already exists'
                }), 409
        
        # Check if RFID tag already exists
        if rfid_tag:
            existing_rfid = get_user_by_rfid(rfid_tag)
            if existing_rfid:
                return jsonify({
                    'status': 'error',
                    'message': 'User with this RFID tag already exists'
                }), 409
        
        # Create user
        user_id = create_user(
            name=name,
            email=email,
            password=password,
            phone_number=phone_number,
            student_id=student_id,
            rfid_tag=rfid_tag
        )
        
        if user_id:
            return jsonify({
                'status': 'success',
                'message': 'User registered successfully',
                'user_id': user_id
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to register user'
            }), 500
    
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Registration failed',
            'error': str(e)
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout endpoint."""
    try:
        session.clear()
        return jsonify({
            'status': 'success',
            'message': 'Logout successful'
        })
    
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Logout failed',
            'error': str(e)
        }), 500

@auth_bp.route('/session', methods=['GET'])
def get_session():
    """Get current session info."""
    try:
        if 'user_id' in session:
            return jsonify({
                'status': 'success',
                'authenticated': True,
                'user_id': session['user_id'],
                'email': session.get('email')
            })
        else:
            return jsonify({
                'status': 'success',
                'authenticated': False
            })
    
    except Exception as e:
        logger.error(f"Session check error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Session check failed',
            'error': str(e)
        }), 500

@auth_bp.route('/rfid-login', methods=['POST'])
def rfid_login():
    """RFID-based login endpoint."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        rfid_tag = data.get('rfid_tag')
        
        if not rfid_tag:
            return jsonify({
                'status': 'error',
                'message': 'RFID tag is required'
            }), 400
        
        # Get user by RFID
        user = get_user_by_rfid(rfid_tag)
        
        if user:
            # Store user ID in session
            session['user_id'] = user['user_id']
            session['email'] = user['email']
            
            return jsonify({
                'status': 'success',
                'message': 'RFID login successful',
                'user': {
                    'user_id': user['user_id'],
                    'name': user['name'],
                    'email': user['email'],
                    'student_id': user['student_id'],
                    'items_found': user['items_found'],
                    'items_find': user['items_find']
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'RFID tag not found'
            }), 404
    
    except Exception as e:
        logger.error(f"RFID login error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'RFID login failed',
            'error': str(e)
        }), 500