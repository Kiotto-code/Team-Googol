from flask import Blueprint, request, jsonify
from database import (
    add_finder, get_finder_by_id, get_finder_by_email, get_finder_by_rfid, get_all_finders,
    add_collector, get_collector_by_id, get_collector_by_email, get_collector_by_student_id, get_all_collectors,
    update_finder_stats, update_collector_stats
)

users_bp = Blueprint('users', __name__)

# FINDER routes
@users_bp.route('/finder/register', methods=['POST'])
def register_finder():
    """Register a new finder in the system."""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "name is required"}), 400
    
    name = data['name']
    email = data.get('email')
    phone = data.get('phone')
    rfid_tag = data.get('rfid_tag')
    
    try:
        # Check if email already exists
        if email and get_finder_by_email(email):
            return jsonify({"error": "Email already exists"}), 409
        
        # Check if RFID tag already exists
        if rfid_tag and get_finder_by_rfid(rfid_tag):
            return jsonify({"error": "RFID tag already exists"}), 409
        
        finder_id = add_finder(name, email, phone, rfid_tag)
        
        return jsonify({
            "message": "Finder registered successfully",
            "finder_id": finder_id,
            "name": name,
            "email": email,
            "phone": phone,
            "rfid_tag": rfid_tag,
            "user_type": "finder"
        }), 201
    except Exception as e:
        return jsonify({"error": f"Failed to register finder: {str(e)}"}), 500

@users_bp.route('/finder/<int:finder_id>', methods=['GET'])
def get_finder_info(finder_id):
    """Get finder information by finder ID."""
    try:
        finder = get_finder_by_id(finder_id)
        if not finder:
            return jsonify({"error": "Finder not found"}), 404
        
        return jsonify({
            "finder_id": finder['finder_id'],
            "name": finder['name'],
            "email": finder['email'],
            "phone": finder['phone'],
            "rfid_tag": finder['rfid_tag'],
            "items_found": finder['items_found'],
            "reputation_score": finder['reputation_score'],
            "created_at": finder['created_at'],
            "last_active": finder['last_active'],
            "user_type": "finder"
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get finder: {str(e)}"}), 500

@users_bp.route('/finder/rfid/<rfid_tag>', methods=['GET'])
def get_finder_by_rfid_tag(rfid_tag):
    """Get finder information by RFID tag."""
    try:
        finder = get_finder_by_rfid(rfid_tag)
        if not finder:
            return jsonify({"error": "Finder not found"}), 404
        
        return jsonify({
            "finder_id": finder['finder_id'],
            "name": finder['name'],
            "email": finder['email'],
            "phone": finder['phone'],
            "rfid_tag": finder['rfid_tag'],
            "items_found": finder['items_found'],
            "reputation_score": finder['reputation_score'],
            "user_type": "finder"
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get finder: {str(e)}"}), 500

@users_bp.route('/finders', methods=['GET'])
def get_all_finders_list():
    """Get all finders in the system."""
    try:
        finders = get_all_finders()
        finders_data = []
        
        for finder in finders:
            finders_data.append({
                "finder_id": finder['finder_id'],
                "name": finder['name'],
                "email": finder['email'],
                "phone": finder['phone'],
                "rfid_tag": finder['rfid_tag'],
                "items_found": finder['items_found'],
                "reputation_score": finder['reputation_score'],
                "created_at": finder['created_at'],
                "last_active": finder['last_active']
            })
        
        return jsonify({
            "finders": finders_data,
            "total_finders": len(finders_data)
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get finders: {str(e)}"}), 500

# COLLECTOR routes
@users_bp.route('/collector/register', methods=['POST'])
def register_collector():
    """Register a new collector (item claimer) in the system."""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "name is required"}), 400
    
    name = data['name']
    email = data.get('email')
    phone = data.get('phone')
    student_id = data.get('student_id')
    id_number = data.get('id_number')
    
    try:
        # Check if email already exists
        if email and get_collector_by_email(email):
            return jsonify({"error": "Email already exists"}), 409
        
        # Check if student ID already exists
        if student_id and get_collector_by_student_id(student_id):
            return jsonify({"error": "Student ID already exists"}), 409
        
        collector_id = add_collector(name, email, phone, student_id, id_number)
        
        return jsonify({
            "message": "Collector registered successfully",
            "collector_id": collector_id,
            "name": name,
            "email": email,
            "phone": phone,
            "student_id": student_id,
            "id_number": id_number,
            "user_type": "collector"
        }), 201
    except Exception as e:
        return jsonify({"error": f"Failed to register collector: {str(e)}"}), 500

@users_bp.route('/collector/<int:collector_id>', methods=['GET'])
def get_collector_info(collector_id):
    """Get collector information by collector ID."""
    try:
        collector = get_collector_by_id(collector_id)
        if not collector:
            return jsonify({"error": "Collector not found"}), 404
        
        return jsonify({
            "collector_id": collector['collector_id'],
            "name": collector['name'],
            "email": collector['email'],
            "phone": collector['phone'],
            "student_id": collector['student_id'],
            "id_number": collector['id_number'],
            "items_claimed": collector['items_claimed'],
            "verification_status": collector['verification_status'],
            "created_at": collector['created_at'],
            "last_active": collector['last_active'],
            "user_type": "collector"
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get collector: {str(e)}"}), 500

@users_bp.route('/collector/student/<student_id>', methods=['GET'])
def get_collector_by_student(student_id):
    """Get collector information by student ID."""
    try:
        collector = get_collector_by_student_id(student_id)
        if not collector:
            return jsonify({"error": "Collector not found"}), 404
        
        return jsonify({
            "collector_id": collector['collector_id'],
            "name": collector['name'],
            "email": collector['email'],
            "phone": collector['phone'],
            "student_id": collector['student_id'],
            "verification_status": collector['verification_status'],
            "user_type": "collector"
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get collector: {str(e)}"}), 500

@users_bp.route('/collectors', methods=['GET'])
def get_all_collectors_list():
    """Get all collectors in the system."""
    try:
        collectors = get_all_collectors()
        collectors_data = []
        
        for collector in collectors:
            collectors_data.append({
                "collector_id": collector['collector_id'],
                "name": collector['name'],
                "email": collector['email'],
                "phone": collector['phone'],
                "student_id": collector['student_id'],
                "items_claimed": collector['items_claimed'],
                "verification_status": collector['verification_status'],
                "created_at": collector['created_at'],
                "last_active": collector['last_active']
            })
        
        return jsonify({
            "collectors": collectors_data,
            "total_collectors": len(collectors_data)
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get collectors: {str(e)}"}), 500

# Combined/utility routes
@users_bp.route('/user/search', methods=['GET'])
def search_user():
    """Search for user by email across both finders and collectors."""
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "email parameter is required"}), 400
    
    try:
        # Check finders first
        finder = get_finder_by_email(email)
        if finder:
            return jsonify({
                "found": True,
                "user_type": "finder",
                "user_id": finder['finder_id'],
                "name": finder['name'],
                "email": finder['email']
            }), 200
        
        # Check collectors
        collector = get_collector_by_email(email)
        if collector:
            return jsonify({
                "found": True,
                "user_type": "collector", 
                "user_id": collector['collector_id'],
                "name": collector['name'],
                "email": collector['email']
            }), 200
        
        return jsonify({
            "found": False,
            "message": "No user found with this email"
        }), 404
        
    except Exception as e:
        return jsonify({"error": f"Failed to search user: {str(e)}"}), 500

@users_bp.route('/users/stats', methods=['GET'])
def get_user_stats():
    """Get statistics about users in the system."""
    try:
        finders = get_all_finders()
        collectors = get_all_collectors()
        
        return jsonify({
            "total_finders": len(finders),
            "total_collectors": len(collectors),
            "active_finders": len([f for f in finders if f['items_found'] > 0]),
            "active_collectors": len([c for c in collectors if c['items_claimed'] > 0]),
            "verified_collectors": len([c for c in collectors if c['verification_status'] == 'verified'])
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get user stats: {str(e)}"}), 500
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "user_id": user['user_id'],
            "name": user['name'],
            "email": user['email'],
            "rfid_tag": user['rfid_tag'],
            "user_type": user['user_type'],
            "created_at": user['created_at'],
            "last_active": user['last_active']
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get user: {str(e)}"}), 500

@users_bp.route('/user/by-email/<email>', methods=['GET'])
def get_user_by_email_route(email):
    """Get user information by email."""
    try:
        user = get_user_by_email(email)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "user_id": user['user_id'],
            "name": user['name'],
            "email": user['email'],
            "rfid_tag": user['rfid_tag'],
            "user_type": user['user_type'],
            "created_at": user['created_at'],
            "last_active": user['last_active']
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get user: {str(e)}"}), 500

@users_bp.route('/user/by-rfid/<rfid_tag>', methods=['GET'])
def get_user_by_rfid_route(rfid_tag):
    """Get user information by RFID tag."""
    try:
        user = get_user_by_rfid(rfid_tag)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "user_id": user['user_id'],
            "name": user['name'],
            "email": user['email'],
            "rfid_tag": user['rfid_tag'],
            "user_type": user['user_type'],
            "created_at": user['created_at'],
            "last_active": user['last_active']
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get user: {str(e)}"}), 500

@users_bp.route('/users', methods=['GET'])
def get_users():
    """Get all users in the system."""
    try:
        users = get_all_users()
        users_data = []
        
        for user in users:
            users_data.append({
                "user_id": user['user_id'],
                "name": user['name'],
                "email": user['email'],
                "rfid_tag": user['rfid_tag'],
                "user_type": user['user_type'],
                "created_at": user['created_at'],
                "last_active": user['last_active']
            })
        
        return jsonify({
            "users": users_data,
            "total_users": len(users_data)
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get users: {str(e)}"}), 500

@users_bp.route('/user/<int:user_id>/activity', methods=['POST'])
def update_user_activity(user_id):
    """Update user's last active timestamp."""
    try:
        success = update_user_last_active(user_id)
        if not success:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "message": "User activity updated successfully",
            "user_id": user_id
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to update user activity: {str(e)}"}), 500
