import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from clip_utils import get_image_embedding, get_text_embedding, save_data, image_data, UPLOAD_FOLDER
from caption_utils import generate_caption_with_gemini
from upload_utils import is_lighting_good, check_framing

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    # Lighting check
    good, brightness, contrast = is_lighting_good(filepath)
    if not good:
        os.remove(filepath)
        return jsonify({
            "error": "Lighting is not good enough, please re-upload.",
            "brightness": brightness,
            "contrast": contrast
        }), 400
        
    # Framing check
    framing_good, framing_msg = check_framing(filepath)
    if not framing_good:
        os.remove(filepath)
        return jsonify({
            "error": "Framing issue: " + framing_msg,
        }), 400


    # User optional description
    description = request.form.get('description', "")

    # --- Generate caption with Gemini ---
    # custom_prompt = "Describe item: color, type, material, unique features. Be concise, no filler."
    custom_prompt = "Output as: Color: <…>; Type: <…>; Material: <…>; Features: <…>; Optional: Brand/Markings: <…>."
    gemini_caption = generate_caption_with_gemini(filepath, prompt=custom_prompt)

    # Combine user description and Gemini caption
    combined_caption = description + ". " + gemini_caption if description else gemini_caption

    # Compute embeddings
    img_emb = get_image_embedding(filepath).detach().cpu().numpy().flatten().tolist()
    desc_emb = get_text_embedding(combined_caption).detach().cpu().numpy().flatten().tolist()

    # Store in memory
    image_data[filename] = {
        "image_embedding": img_emb,
        "description": description,
        "gemini_caption": gemini_caption,
        "description_embedding": desc_emb
    }
    save_data()

    return jsonify({
        "message": "Image uploaded successfully",
        "filename": filename,
        "description": description,
        "gemini_caption": gemini_caption
    }), 200