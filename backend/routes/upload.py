import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from clip_utils import get_image_embedding, save_data, image_data, UPLOAD_FOLDER

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    file = request.files['image']
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    embedding = get_image_embedding(filepath).cpu().numpy().tolist()
    image_data[filename] = embedding
    save_data()

    return jsonify({"message": "Image uploaded successfully", "filename": filename})
