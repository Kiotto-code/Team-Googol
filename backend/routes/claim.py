from flask import Blueprint, request, jsonify
from database import claim_item, get_all_items, release_expired_claims

claim_bp = Blueprint('claim', __name__)

@claim_bp.route('/claim', methods=['POST'])
def claim_found_item():
    """Claim a found item for 1 hour."""
    data = request.get_json()
    
    if 'item_id' not in data:
        return jsonify({"error": "No item_id provided"}), 400
    
    if 'claimed_by' not in data:
        return jsonify({"error": "No claimed_by (user identifier) provided"}), 400
    
    item_id = data['item_id']
    claimed_by = data['claimed_by']
    
    # Clean up expired claims first
    released_count = release_expired_claims()
    if released_count > 0:
        print(f"Released {released_count} expired claims")
    
    success, message = claim_item(item_id, claimed_by)
    
    if success:
        return jsonify({"message": message}), 200
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
