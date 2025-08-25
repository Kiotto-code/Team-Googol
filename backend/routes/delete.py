import os
from flask import Blueprint, request, jsonify
from clip_utils import image_data, save_data, UPLOAD_FOLDER

delete_bp = Blueprint('delete', __name__)

@delete_bp.route('/delete', methods=['POST'])
def delete_image():
    data = request.get_json()
    if 'filename' not in data:
        return jsonify({"error": "No filename provided"}), 400

    filename = data['filename']
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
    else:
        return jsonify({"error": "Image file not found"}), 404

    if filename in image_data:
        del image_data[filename]
        save_data()
    else:
        return jsonify({"error": "Embedding not found in data.json"}), 404

    return jsonify({"message": f"{filename} deleted successfully"})