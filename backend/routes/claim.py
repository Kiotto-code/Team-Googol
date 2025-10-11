from flask import Blueprint, jsonify, request

from database import (
    claim_case,
    get_case,
    get_user_by_email,
    get_user_by_student_id,
    list_cases,
    release_expired_cases,
)

claim_bp = Blueprint("claim", __name__)


@claim_bp.route("/claim", methods=["POST"])
def claim_case_endpoint():
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    case_id = data.get("case_id") or data.get("found_id")
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400

    try:
        case_id = int(case_id)
    except (TypeError, ValueError):
        return jsonify({"error": "case_id must be an integer"}), 400

    receiver_id = data.get("receiver_id")
    email = data.get("email")
    student_id = data.get("student_id")

    if receiver_id:
        try:
            receiver_id = int(receiver_id)
        except (TypeError, ValueError):
            return jsonify({"error": "receiver_id must be an integer"}), 400

    if not receiver_id and not email and not student_id:
        return jsonify({"error": "Provide receiver_id, email, or student_id"}), 400

    if not receiver_id and email:
        user = get_user_by_email(email)
        if not user:
            return jsonify({"error": "email not registered", "email": email}), 404
        receiver_id = user["user_id"]

    if not receiver_id and student_id:
        user = get_user_by_student_id(student_id)
        if not user:
            return jsonify({"error": "student id not registered", "student_id": student_id}), 404
        receiver_id = user["user_id"]

    release_expired_cases()
    success, message = claim_case(case_id, receiver_id)

    if success:
        case = get_case(case_id)
        return jsonify({
            "message": message,
            "case_id": case_id,
            "receiver_id": receiver_id,
            "case_status": case["status"] if case else "claimed",
            "case_close_at": case["case_close_at"] if case else None,
        })

    return jsonify({"error": message}), 400


@claim_bp.route("/cases", methods=["GET"])
def list_all_cases():
    release_expired_cases()
    cases = list_cases()

    response = []
    for case in cases:
        response.append(
            {
                "case_id": case["found_id"],
                "status": case["status"],
                "box_id": case["box_id"],
                "item_id": case["item_id"],
                "receiver_id": case["reciver_id"],
                "case_close_at": case["case_close_at"],
                "created_at": case["created_at"],
                "item_description": case["description"],
                "item_image_url": case["image_url"],
                "box_location": case["location"],
            }
        )

    return jsonify({"cases": response, "total": len(response)})


@claim_bp.route("/release-expired", methods=["POST"])
def release_expired():
    released_count = release_expired_cases()
    return jsonify({
        "message": f"Released {released_count} expired claims",
        "released_count": released_count,
    })
