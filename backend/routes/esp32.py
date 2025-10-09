import os
from datetime import datetime
from flask import request, jsonify, Blueprint

esp32_bp = Blueprint("esp32", __name__)
ESP32_UPLOAD_FOLDER = "esp32_uploads"
os.makedirs(ESP32_UPLOAD_FOLDER, exist_ok=True)

def get_next_image_id():
    """Get the next incremental ID based on files in the upload folder."""
    # Count existing images across supported extensions
    existing_files = [
        f for f in os.listdir(ESP32_UPLOAD_FOLDER)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    if not existing_files:
        return 1
    ids = []
    for f in existing_files:
        try:
            ids.append(int(f.split("_")[0]))  # get the numeric ID before "_"
        except ValueError:
            continue
    return max(ids) + 1 if ids else 1

@esp32_bp.route("/esp32/upload/image", methods=["POST"])
def esp32_upload_image():
    """
    Endpoint for ESP32-CAM to upload a JPEG/PNG image.
    The image will be saved with an incrementing ID and timestamp in the filename.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        # Generate filename with increment ID + timestamp
        img_id = get_next_image_id()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Preserve the original extension (normalized to lowercase)
        _, ext = os.path.splitext(file.filename)
        ext = ext.lower()
        filename = f"{img_id}_{timestamp}{ext}"
        filepath = os.path.join(ESP32_UPLOAD_FOLDER, filename)

        file.save(filepath)

        return jsonify({
            "message": "ESP32 image uploaded successfully",
            "filename": filename,
            "path": filepath,
            "image_id": img_id
        }), 201
    else:
        return jsonify({"error": "Only .jpg/.jpeg/.png files are allowed"}), 400
