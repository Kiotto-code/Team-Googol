import os
import time

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from clip_utils import COLLECTOR_FOLDER, get_image_embedding
from database import (
    add_case,
    add_found_item,
    get_box_status,
    get_user_by_rfid,
    update_box,
    update_finder_stats,
)

collect_bp = Blueprint('collect', __name__)


@collect_bp.route('/collect', methods=['POST'])
def collect_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image collected"}), 400

    # Get form data
    imgtaken_timestamp = request.form.get('timestamp', "")
    box_id_raw = request.form.get('box_id', "").strip()
    finder_rfid = request.form.get('finder_rfid', "").strip()  # RFID tag of the person who found the item
    collector_img = request.files['image']

    # Look up finder by RFID if provided
    finder_id = None
    if finder_rfid:
        finder = get_user_by_rfid(finder_rfid)
        if finder:
            finder_id = finder['user_id']
        else:
            return jsonify({
                "error": "Finder RFID not registered in system",
                "rfid_tag": finder_rfid,
                "suggestion": "Please register this RFID tag first using /finder/register"
            }), 400

    # Validate box_id if provided
    box_id = None
    box_info = None
    if box_id_raw:
        try:
            box_id = int(box_id_raw)
        except ValueError:
            return jsonify({"error": "box_id must be an integer"}), 400

        box_info = get_box_status(box_id)
        if not box_info:
            return jsonify({"error": f"Box with id '{box_id}' not found"}), 404

    # Generate secure filename
    filename = secure_filename(collector_img.filename)
    if not filename:
        filename = f"collected_{int(time.time())}.jpg"

    filepath = os.path.join(COLLECTOR_FOLDER, filename)
    collector_img.save(filepath)

    request_received_timestamp = time.time()

    # Convert timestamp to float for comparison
    try:
        img_timestamp = float(imgtaken_timestamp) if imgtaken_timestamp else request_received_timestamp
    except ValueError:
        img_timestamp = request_received_timestamp

    if request_received_timestamp - img_timestamp > 10:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": "Timestamp Exceeded 5 seconds"}), 400

    # Compute image embedding for downstream similarity search
    try:
        image_embedding = (
            get_image_embedding(filepath)
            .detach()
            .cpu()
            .numpy()
            .flatten()
            .tolist()
        )
    except Exception as embedding_error:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": f"Failed to compute image embedding: {embedding_error}"}), 500

    try:
        # Save to database with finder information and embedding metadata
        item_id = add_found_item(
            filename,
            image_embedding=image_embedding,
            description="",
            description_embedding=None,
            finder_user_id=finder_id,
            box_id=box_id,
            imgtaken_timestamp=img_timestamp,
            status='collected',
        )

        if finder_id:
            update_finder_stats(finder_id, items_found_increment=1)

        if box_id is not None:
            # Create a case tied to this box to track the new item
            add_case(box_id, item_id=item_id, status='pending_deposit')

            # Update the box load and availability status
            capacity_raw = box_info.get('capacity') if box_info else None
            try:
                capacity = int(capacity_raw) if capacity_raw is not None else None
            except (TypeError, ValueError):
                capacity = None

            current_load_raw = None
            if box_info:
                current_load_raw = box_info.get('load', box_info.get('current_load'))
            try:
                current_load = int(current_load_raw) if current_load_raw is not None else 0
            except (TypeError, ValueError):
                current_load = 0

            new_load = current_load + 1
            is_available = True
            if capacity is not None and capacity > 0:
                is_available = new_load < capacity

            update_box(box_id, load=new_load, status=is_available)

        return jsonify({
            "message": "Image collected successfully",
            "filename": filename,
            "item_id": item_id,
            "box_id": box_id,
            "finder_id": finder_id,
            "timestamp": img_timestamp
        }), 200
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": f"Failed to save item: {str(e)}"}), 500
