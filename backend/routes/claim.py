from flask import Blueprint, request, jsonify
from database import claim_item, get_all_items, release_expired_claims, get_collector_by_email, get_collector_by_student_id

claim_bp = Blueprint('claim', __name__)

@claim_bp.route('/claim', methods=['POST'])
def claim_found_item():
    """Claim a found item for 1 hour."""
    data = request.get_json()
    
    if 'item_id' not in data:
        return jsonify({"error": "No item_id provided"}), 400
    
    # Accept either collector_id directly, email, or student_id to look up collector
    collector_id = data.get('collector_id')
    email = data.get('email')
    student_id = data.get('student_id')
    
    if not collector_id and not email and not student_id:
        return jsonify({"error": "Either collector_id, email, or student_id must be provided"}), 400
    
    # If email provided, look up collector
    if email and not collector_id:
        collector = get_collector_by_email(email)
        if not collector:
            return jsonify({
                "error": "Email not registered in system",
                "email": email,
                "suggestion": "Please register this email first using /collector/register"
            }), 400
        collector_id = collector['collector_id']
    
    # If student_id provided, look up collector
    if student_id and not collector_id:
        collector = get_collector_by_student_id(student_id)
        if not collector:
            return jsonify({
                "error": "Student ID not registered in system", 
                "student_id": student_id,
                "suggestion": "Please register this student ID first using /collector/register"
            }), 400
        collector_id = collector['collector_id']
    
    item_id = data['item_id']
    
    # Clean up expired claims first
    released_count = release_expired_claims()
    if released_count > 0:
        print(f"Released {released_count} expired claims")
    
    success, message = claim_item(item_id, collector_id)
    
    if success:
        return jsonify({
            "message": message,
            "collector_id": collector_id,
            "item_id": item_id
        }), 200
    else:
        return jsonify({"error": message}), 400

@claim_bp.route('/items', methods=['GET'])
def list_all_items():
    """List all items in the FOUND_ITEMS table with their status."""
    # Clean up expired claims first
    release_expired_claims()
    
    items = get_all_items()
    
    result = []
    for item in items:
        result.append({
            'id': item['id'],
            'filename': item['filename'],
            'description': item['description'],
            'status': item['status'],
            'claimed_by': item['claimed_by'],
            'claimed_at': item['claimed_at'],
            'expires_at': item['expires_at'],
            'uploaded_at': item['uploaded_at'],
            'url': f"http://127.0.0.1:5000/uploads/{item['filename']}"
        })
    
    return jsonify({"items": result})

@claim_bp.route('/release-expired', methods=['POST'])
def release_expired():
    """Manually release expired claims (for maintenance)."""
    released_count = release_expired_claims()
    return jsonify({
        "message": f"Released {released_count} expired claims",
        "released_count": released_count
    })
