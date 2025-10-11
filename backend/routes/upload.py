import os
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from caption_utils import generate_caption_with_gemini
from database import create_item
from upload_utils import is_lighting_good
from clip_utils import UPLOAD_FOLDER

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/upload", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    filename = secure_filename(file.filename) or "uploaded_item.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    good, brightness, contrast = is_lighting_good(filepath)
    if not good:
        os.remove(filepath)
        return (
            jsonify(
                {
                    "error": "Lighting is not good enough, please re-upload.",
                    "brightness": brightness,
                    "contrast": contrast,
                }
            ),
            400,
        )

    description = request.form.get("description", "")
    finder_user_id = request.form.get("finder_user_id")
    finder_img_url = request.form.get("finder_img_url")
    box_id = request.form.get("box_id")  # forwarded for clients that associate immediately

    finder_id_value = None
    if finder_user_id:
        try:
            finder_id_value = int(finder_user_id)
        except ValueError:
            os.remove(filepath)
            return jsonify({"error": "finder_user_id must be an integer"}), 400

    custom_prompt = (
        "Output as: Color: <…>; Type: <…>; Material: <…>; Features: <…>; Optional: Brand/Markings: <…>."
    )
    gemini_caption = generate_caption_with_gemini(filepath, prompt=custom_prompt)
    combined_caption = f"{description}. {gemini_caption}" if description else gemini_caption

    try:
        item_id = create_item(
            description=combined_caption,
            image_url=filename,
            finder_user_id=finder_id_value,
            finder_img_url=finder_img_url,
        )

        response = {
            "message": "Image uploaded successfully",
            "filename": filename,
            "description": combined_caption,
            "item_id": item_id,
        }
        if box_id:
            response["box_id"] = box_id
        return jsonify(response)
    except Exception as exc:  # pragma: no cover - sqlite safety net
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": f"Failed to save item: {exc}"}), 500
