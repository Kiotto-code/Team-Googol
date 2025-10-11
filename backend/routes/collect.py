import os
import time
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from clip_utils import COLLECTOR_FOLDER
from database import (
    create_case,
    get_box,
    get_item_by_id,
    increment_user_items_found,
    update_box,
    update_item_finder_image,
)

collect_bp = Blueprint("collect", __name__)


@collect_bp.route("/collect", methods=["POST"])
def collect_item():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    form = request.form.to_dict()
    item_id = form.get("item_id")
    box_id = form.get("box_id")

    if not item_id:
        return jsonify({"error": "item_id is required"}), 400
    if not box_id:
        return jsonify({"error": "box_id is required"}), 400

    try:
        item_id = int(item_id)
        box_id = int(box_id)
    except (TypeError, ValueError):
        return jsonify({"error": "item_id and box_id must be integers"}), 400

    item = get_item_by_id(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    box = get_box(box_id)
    if not box:
        return jsonify({"error": "Box not found"}), 404

    collector_img = request.files["image"]
    filename = secure_filename(collector_img.filename) or f"collected_{int(time.time())}.jpg"
    file_path = os.path.join(COLLECTOR_FOLDER, filename)
    collector_img.save(file_path)

    try:
        update_item_finder_image(item_id, filename)

        if item["finder_user_id"]:
            increment_user_items_found(item["finder_user_id"], 1)

        new_load = (box["load"] or 0) + 1
        update_box(
            box_id,
            load=new_load,
            status=new_load == 0,
            door_status=False,
        )

        case_status = form.get("status", "available")
        receiver_id = form.get("receiver_id")
        receiver_image_url = form.get("receiver_image_url")
        case_close_at = form.get("case_close_at")
        receiver_id_value = None
        if receiver_id:
            try:
                receiver_id_value = int(receiver_id)
            except (TypeError, ValueError):
                return jsonify({"error": "receiver_id must be an integer"}), 400

        case_id = create_case(
            box_id=box_id,
            reciver_image_url=receiver_image_url or filename,
            reciver_id=receiver_id_value,
            item_id=item_id,
            status=case_status,
            case_close_at=case_close_at,
        )

        return jsonify({
            "message": "Item collected and case created",
            "item_id": item_id,
            "box_id": box_id,
            "case_id": case_id,
            "finder_user_id": item["finder_user_id"],
        })
    except Exception as exc:  # pragma: no cover - sqlite safety net
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": f"Failed to process collection: {exc}"}), 500
