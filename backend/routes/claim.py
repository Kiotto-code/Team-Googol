from flask import Blueprint, request, jsonify
from database import (
    claim_item,
    get_items_with_case,
    release_expired_claims,
    get_collector_by_email,
    get_collector_by_student_id,
)

claim_bp = Blueprint('claim', __name__)

@claim_bp.route('/claim', methods=['POST'])
def claim_found_item():
    """Claim a found item for 1 hour.
    Accepts JSON or form data. You can provide one of: collector_id, email, or student_id.
    For convenience, if a 'claimed_by' field looks like an email, it's treated as 'email'.
    """
    # Support JSON or form submissions
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    item_id = data.get('item_id')
    if not item_id:
        return jsonify({"error": "No item_id provided"}), 400

    # Accept either collector_id directly, email, or student_id to look up collector
    collector_id = data.get('collector_id')
    email = data.get('email')
    student_id = data.get('student_id')

    # Backward-compat: if frontend sent 'claimed_by' and it looks like an email, use it
    claimed_by = data.get('claimed_by')
    if not email and claimed_by and isinstance(claimed_by, str) and '@' in claimed_by:
        email = claimed_by

    if not collector_id and not email and not student_id:
        return jsonify({
            "error": "Either collector_id, email, or student_id must be provided",
            "hint": "Send JSON like { item_id, email } or { item_id, collector_id }"
        }), 400

    # If email provided, look up collector
    if email and not collector_id:
        collector = get_collector_by_email(email)
        if not collector:
            return jsonify({
                "error": "Email not registered in system",
                "email": email,
                "suggestion": "Please register this email first using /collector/register"
            }), 400
        # Unified USERS schema uses 'user_id'
        collector_id = collector['user_id']

    # If student_id provided, look up collector
    if student_id and not collector_id:
        collector = get_collector_by_student_id(student_id)
        if not collector:
            return jsonify({
                "error": "Student ID not registered in system",
                "student_id": student_id,
                "suggestion": "Please register this student ID first using /collector/register"
            }), 400
        # Unified USERS schema uses 'user_id'
        collector_id = collector['user_id']

    # Clean up expired claims first (best-effort; ignore transient lock errors)
    try:
        released_count = release_expired_claims()
        if released_count > 0:
            print(f"Released {released_count} expired claims")
    except Exception as e:
        print(f"Warning: release_expired_claims skipped due to: {e}")

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
    """List claimable inventory derived from the Item and Case tables."""
    # Clean up expired claims first
    release_expired_claims()
    
    items = get_items_with_case()

    result = []
    for item in items:
        result.append({
            'id': item['id'],
            'filename': item['filename'],
            'description': item['description'],
            'status': item.get('status'),
            'claimed_by': item.get('claimed_by'),
            'claimed_at': item.get('claimed_at'),
            'expires_at': item.get('expires_at'),
            'uploaded_at': item.get('uploaded_at'),
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
