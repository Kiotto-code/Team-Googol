import os
from flask import Blueprint, jsonify, request

from clip_utils import UPLOAD_FOLDER
from database import delete_item, get_item_by_id, get_item_by_image_url

delete_bp = Blueprint("delete", __name__)


@delete_bp.route("/delete", methods=["POST"])
def delete_image():
    data = request.get_json() or {}
    item_id = data.get("item_id")
    image_url = data.get("image_url") or data.get("filename")

    if not item_id and not image_url:
        return jsonify({"error": "item_id or image_url is required"}), 400

    item = None
    if item_id:
        try:
            item_id = int(item_id)
        except (TypeError, ValueError):
            return jsonify({"error": "item_id must be an integer"}), 400
        item = get_item_by_id(item_id)
    elif image_url:
        item = get_item_by_image_url(image_url)

    if not item:
        return jsonify({"error": "Item not found"}), 404

    filename = item["image_url"]
    if filename:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            os.remove(filepath)

    deleted = delete_item(item["item_id"])
    if not deleted:
        return jsonify({"error": "Failed to delete from database"}), 500

    return jsonify({"message": "Item deleted", "item_id": item["item_id"]})
