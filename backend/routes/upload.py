import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from clip_utils import get_image_embedding, get_text_embedding, save_data, image_data, UPLOAD_FOLDER
from caption_utils import generate_caption 

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # User optional description
    description = request.form.get('description', "")

    # --- Generate BLIP caption ---
    custom_prompt = "Describe the lost item including color, type, material, and any unique features."
    # blip_caption = generate_caption(filepath, prompt=custom_prompt)
    blip_caption = generate_caption(filepath) 

    # Choose combined text: user description + BLIP caption
    combined_caption = description + ". " + blip_caption if description else blip_caption

    # --- Compute embeddings ---
    img_emb = get_image_embedding(filepath).detach().cpu().numpy().flatten().tolist()
    desc_emb = get_text_embedding(combined_caption).detach().cpu().numpy().flatten().tolist()

    # Store both raw captions and embedding
    image_data[filename] = {
        "image_embedding": img_emb,
        "description": description,
        "blip_caption": blip_caption,
        "description_embedding": desc_emb
    }
    save_data()

    return jsonify({
        "message": "Image uploaded successfully",
        "filename": filename,
        "description": description,
        "blip_caption": blip_caption
    }), 200

