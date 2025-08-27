from flask import Blueprint, jsonify
import os
from clip_utils import UPLOAD_FOLDER, save_data, image_data

delete_all_bp = Blueprint('delete_all', __name__)

@delete_all_bp.route('/delete_all', methods=['POST'])
def delete_all_images():
    # Delete all files in the upload folder
    deleted_files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            deleted_files.append(filename)
    
    # Clear the JSON metadata
    image_data.clear()
    save_data()

    return jsonify({
        "message": "All images and their metadata have been deleted",
        "deleted_files": deleted_files
    }), 200
