import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from clip_utils import get_image_embedding, get_text_embedding, UPLOAD_FOLDER
from database import add_found_item

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

    try:
        # Save to database
        item_id = add_found_item(filename, img_emb, description, desc_emb)
        return jsonify({
            "message": "Image uploaded successfully", 
            "filename": filename,
            "item_id": item_id
        }), 200
    except Exception as e:
        # Remove uploaded file if database save fails
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": f"Failed to save item: {str(e)}"}), 500
