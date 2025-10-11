from flask import Blueprint, jsonify, request

from database import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_rfid,
    get_user_by_student_id,
    increment_user_items_claimed,
    increment_user_items_found,
    list_users,
)

users_bp = Blueprint("users", __name__)


@users_bp.route("/users/register", methods=["POST"])
def register_user():
    data = request.get_json() or {}

    name = data.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400

    password = data.get("password")
    phone_number = data.get("phone_number")
    email = data.get("email")
    student_id = data.get("student_id")
    rfid_tag = data.get("rfid_tag")

    try:
        if email and get_user_by_email(email):
            return jsonify({"error": "email already registered"}), 409

        if rfid_tag and get_user_by_rfid(rfid_tag):
            return jsonify({"error": "rfid tag already registered"}), 409

        if student_id and get_user_by_student_id(student_id):
            return jsonify({"error": "student id already registered"}), 409

        user_id = create_user(
            name=name,
            password=password,
            phone_number=phone_number,
            email=email,
            student_id=student_id,
            rfid_tag=rfid_tag,
        )

        user = get_user_by_id(user_id)
        return (
            jsonify(
                {
                    "message": "User registered successfully",
                    "user": {
                        "user_id": user["user_id"],
                        "name": user["name"],
                        "email": user["email"],
                        "phone_number": user["phone_number"],
                        "student_id": user["student_id"],
                        "rfid_tag": user["rfid_tag"],
                        "items_found": user["items_found"],
                        "items_find": user["items_find"],
                        "created_at": user["created_at"],
                    },
                }
            ),
            201,
        )
    except Exception as exc:  # pragma: no cover - safety net for unexpected sqlite errors
        return jsonify({"error": f"failed to register user: {exc}"}), 500


@users_bp.route("/users/<int:user_id>", methods=["GET"])
def retrieve_user(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    return (
        jsonify(
            {
                "user_id": user["user_id"],
                "name": user["name"],
                "email": user["email"],
                "phone_number": user["phone_number"],
                "student_id": user["student_id"],
                "rfid_tag": user["rfid_tag"],
                "items_found": user["items_found"],
                "items_find": user["items_find"],
                "created_at": user["created_at"],
            }
        ),
        200,
    )


@users_bp.route("/users", methods=["GET"])
def retrieve_users():
    users = list_users()
    payload = [
        {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"],
            "phone_number": user["phone_number"],
            "student_id": user["student_id"],
            "rfid_tag": user["rfid_tag"],
            "items_found": user["items_found"],
            "items_find": user["items_find"],
            "created_at": user["created_at"],
        }
        for user in users
    ]
    return jsonify({"users": payload, "total": len(payload)})


@users_bp.route("/users/email/<email>", methods=["GET"])
def retrieve_user_by_email(email: str):
    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify({
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "phone_number": user["phone_number"],
        "student_id": user["student_id"],
        "rfid_tag": user["rfid_tag"],
        "items_found": user["items_found"],
        "items_find": user["items_find"],
        "created_at": user["created_at"],
    })


@users_bp.route("/users/rfid/<rfid_tag>", methods=["GET"])
def retrieve_user_by_rfid(rfid_tag: str):
    user = get_user_by_rfid(rfid_tag)
    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify({
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "phone_number": user["phone_number"],
        "student_id": user["student_id"],
        "rfid_tag": user["rfid_tag"],
        "items_found": user["items_found"],
        "items_find": user["items_find"],
        "created_at": user["created_at"],
    })


@users_bp.route("/users/student/<student_id>", methods=["GET"])
def retrieve_user_by_student(student_id: str):
    user = get_user_by_student_id(student_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify({
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "phone_number": user["phone_number"],
        "student_id": user["student_id"],
        "rfid_tag": user["rfid_tag"],
        "items_found": user["items_found"],
        "items_find": user["items_find"],
        "created_at": user["created_at"],
    })


@users_bp.route("/users/<int:user_id>/stats", methods=["POST"])
def update_user_stats(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    data = request.get_json() or {}
    items_found_delta = int(data.get("items_found", 0) or 0)
    items_find_delta = int(data.get("items_find", 0) or 0)

    if items_found_delta:
        increment_user_items_found(user_id, items_found_delta)
    if items_find_delta:
        increment_user_items_claimed(user_id, items_find_delta)

    updated_user = get_user_by_id(user_id)
    return jsonify({
        "message": "stats updated",
        "user": {
            "user_id": updated_user["user_id"],
            "name": updated_user["name"],
            "items_found": updated_user["items_found"],
            "items_find": updated_user["items_find"],
        },
    })
