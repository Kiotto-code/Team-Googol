from flask import Blueprint, jsonify, request

from database import (
    add_collector,
    add_finder,
    get_all_collectors,
    get_all_finders,
    get_all_users,
    get_collector_by_email,
    get_collector_by_id,
    get_collector_by_student_id,
    get_finder_by_email,
    get_finder_by_id,
    get_finder_by_rfid,
    get_user_by_email,
    get_user_by_id,
    get_user_by_rfid,
    update_user_last_active,
)

users_bp = Blueprint('users', __name__)


def _serialise_user(row, role_key=None):
    if not row:
        return None
    row_dict = dict(row)
    data = {
        "user_id": row_dict["user_id"],
        "name": row_dict["name"],
        "email": row_dict.get("email"),
        "phone_number": row_dict.get("phone_number") or row_dict.get("phone"),
        "student_id": row_dict.get("student_id"),
        "rfid_tag": row_dict.get("rfid_tag"),
        "id_number": row_dict.get("id_number"),
        "items_found": row_dict.get("items_found", 0),
        "items_find": row_dict.get("items_find", row_dict.get("items_claimed", 0)),
        "created_at": row_dict.get("created_at"),
        "last_active": row_dict.get("last_active"),
        "role": row_dict.get("role") or row_dict.get("user_type"),
    }
    if role_key:
        data[f"{role_key}_id"] = row_dict["user_id"]
    return data


# ---------------------------------------------------------------------------
# Finder endpoints
# ---------------------------------------------------------------------------

@users_bp.route('/finder/register', methods=['POST'])
def register_finder():
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({"error": "name is required"}), 400

    email = data.get('email')
    phone_number = data.get('phone') or data.get('phone_number')
    rfid_tag = data.get('rfid_tag')
    password = data.get('password')

    if email and get_user_by_email(email):
        return jsonify({"error": "Email already exists"}), 409

    if rfid_tag and get_user_by_rfid(rfid_tag):
        return jsonify({"error": "RFID tag already exists"}), 409

    finder_id = add_finder(name, email=email, phone=phone_number, rfid_tag=rfid_tag, password=password)

    finder = get_finder_by_id(finder_id)
    response = _serialise_user(finder, role_key='finder')
    response.update({
        "message": "Finder registered successfully"
    })
    return jsonify(response), 201


@users_bp.route('/finder/<int:finder_id>', methods=['GET'])
def get_finder_info(finder_id: int):
    finder = get_finder_by_id(finder_id)
    if not finder:
        return jsonify({"error": "Finder not found"}), 404

    data = _serialise_user(finder, role_key='finder')
    return jsonify(data), 200


@users_bp.route('/finder/rfid/<rfid_tag>', methods=['GET'])
def get_finder_by_rfid_tag(rfid_tag: str):
    finder = get_finder_by_rfid(rfid_tag)
    if not finder:
        return jsonify({"error": "Finder not found"}), 404

    return jsonify(_serialise_user(finder, role_key='finder')), 200


@users_bp.route('/finders', methods=['GET'])
def get_all_finders_list():
    finders = [_serialise_user(row, role_key='finder') for row in get_all_finders()]
    return jsonify({
        "finders": finders,
        "total_finders": len(finders)
    }), 200


# ---------------------------------------------------------------------------
# Collector endpoints
# ---------------------------------------------------------------------------

@users_bp.route('/collector/register', methods=['POST'])
def register_collector():
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({"error": "name is required"}), 400

    email = data.get('email')
    phone_number = data.get('phone') or data.get('phone_number')
    student_id = data.get('student_id')
    id_number = data.get('id_number')
    password = data.get('password')

    if email and get_user_by_email(email):
        return jsonify({"error": "Email already exists"}), 409

    if student_id and get_collector_by_student_id(student_id):
        return jsonify({"error": "Student ID already exists"}), 409

    collector_id = add_collector(
        name,
        email=email,
        phone=phone_number,
        student_id=student_id,
        id_number=id_number,
        password=password
    )

    collector = get_collector_by_id(collector_id)
    response = _serialise_user(collector, role_key='collector')
    response.update({
        "message": "Collector registered successfully"
    })
    return jsonify(response), 201


@users_bp.route('/collector/<int:collector_id>', methods=['GET'])
def get_collector_info(collector_id: int):
    collector = get_collector_by_id(collector_id)
    if not collector:
        return jsonify({"error": "Collector not found"}), 404

    return jsonify(_serialise_user(collector, role_key='collector')), 200


@users_bp.route('/collector/student/<student_id>', methods=['GET'])
def get_collector_by_student(student_id: str):
    collector = get_collector_by_student_id(student_id)
    if not collector:
        return jsonify({"error": "Collector not found"}), 404

    return jsonify(_serialise_user(collector, role_key='collector')), 200


@users_bp.route('/collectors', methods=['GET'])
def get_all_collectors_list():
    collectors = [_serialise_user(row, role_key='collector') for row in get_all_collectors()]
    return jsonify({
        "collectors": collectors,
        "total_collectors": len(collectors)
    }), 200


# ---------------------------------------------------------------------------
# Shared/user endpoints
# ---------------------------------------------------------------------------

@users_bp.route('/user/search', methods=['GET'])
def search_user():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "email parameter is required"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"found": False, "message": "No user found with this email"}), 404

    data = _serialise_user(user)
    return jsonify({
        "found": True,
        "user": data
    }), 200


@users_bp.route('/users/stats', methods=['GET'])
def get_user_stats():
    finders = list(get_all_finders())
    collectors = list(get_all_collectors())

    return jsonify({
        "total_finders": len(finders),
        "total_collectors": len(collectors),
        "active_finders": len([f for f in finders if f['items_found'] > 0]),
        "active_collectors": len([c for c in collectors if c['items_find'] > 0])
    }), 200


@users_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_route(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(_serialise_user(user)), 200


@users_bp.route('/user/by-email/<email>', methods=['GET'])
def get_user_by_email_route(email: str):
    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(_serialise_user(user)), 200


@users_bp.route('/user/by-rfid/<rfid_tag>', methods=['GET'])
def get_user_by_rfid_route(rfid_tag: str):
    user = get_user_by_rfid(rfid_tag)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(_serialise_user(user)), 200


@users_bp.route('/users', methods=['GET'])
def get_users():
    users = [_serialise_user(row) for row in get_all_users()]
    return jsonify({
        "users": users,
        "total_users": len(users)
    }), 200


@users_bp.route('/user/<int:user_id>/activity', methods=['POST'])
def update_user_activity(user_id: int):
    if not update_user_last_active(user_id):
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "message": "User activity updated successfully",
        "user_id": user_id
    }), 200
