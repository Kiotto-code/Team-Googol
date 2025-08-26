import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from clip_utils import get_image_embedding, get_text_embedding, save_data, image_data, UPLOAD_FOLDER

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Optional description
    description = request.form.get('description', "")

    # Compute embeddings and move to CPU + NumPy
    img_emb = get_image_embedding(filepath).detach().cpu().numpy().flatten().tolist()

    desc_emb = None
    if description:
        desc_emb = get_text_embedding(description).detach().cpu().numpy().flatten().tolist()

    # Save in memory/dict (ensure JSON-serializable)
    image_data[filename] = {
        "image_embedding": img_emb,
        "description_embedding": desc_emb,
        "description": description
    }
    save_data()

    return jsonify({"message": "Image uploaded successfully", "filename": filename}), 200
