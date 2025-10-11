from flask import Blueprint, jsonify, request

from database import release_expired_cases, search_cases

search_bp = Blueprint("search", __name__)


@search_bp.route("/search", methods=["POST"])
def search_items():
    payload = request.get_json() or {}
    query = (payload.get("query") or "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400

    release_expired_cases()
    rows = search_cases(query)

    if not rows:
        return jsonify({"message": "No matching cases found"}), 404

    def _to_bool(value):
        if value is None:
            return None
        return bool(value)

    results = []
    for row in rows:
        results.append(
            {
                "case_id": row["found_id"],
                "status": row["status"] or "available",
                "case_close_at": row["case_close_at"],
                "created_at": row["created_at"],
                "receiver_id": row["reciver_id"],
                "receiver_image_url": row["reciver_image_url"],
                "item": {
                    "item_id": row["item_id"],
                    "description": row["description"],
                    "image_url": row["image_url"],
                    "finder_user_id": row["finder_user_id"],
                    "finder_img_url": row["finder_img_url"],
                    "finder_name": row["finder_name"],
                },
                "box": {
                    "box_id": row["box_id"],
                    "location": row["location"],
                    "status": _to_bool(row["box_status"]),
                    "load": row["load"],
                    "door_status": _to_bool(row["door_status"]),
                    "last_accessed": row["last_accessed"],
                },
            }
        )

    return jsonify({"results": results, "count": len(results)})
