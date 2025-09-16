import os
from flask import Blueprint, request, jsonify
from clip_utils import UPLOAD_FOLDER
from database import delete_item, get_item_by_filename

delete_bp = Blueprint('delete', __name__)

@delete_bp.route('/delete', methods=['POST'])
def delete_image():
    data = request.get_json()
    if 'filename' not in data:
        return jsonify({"error": "No filename provided"}), 400

    filename = data['filename']
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Check if item exists in database
    item = get_item_by_filename(filename)
    if not item:
        return jsonify({"error": "Item not found in database"}), 404

    # Remove file from filesystem
    if os.path.exists(filepath):
        os.remove(filepath)

    # Remove from database
    deleted = delete_item(filename)
    
    if deleted:
        return jsonify({"message": f"{filename} deleted successfully"})
    else:
        return jsonify({"error": "Failed to delete from database"}), 500