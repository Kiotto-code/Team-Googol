import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

# Absolute path to the SQLite database
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lost_and_found.db")

# Table names from the new schema specification
USER_TABLE = "User"
ITEM_TABLE = "Item"
BOX_TABLE = "Box"
CASE_TABLE = "Case"


# ---------------------------------------------------------------------------
# Database initialisation helpers
# ---------------------------------------------------------------------------
def init_database() -> None:
    """Initialise the database using the new schema design."""
    with sqlite3.connect(DATABASE_PATH, timeout=15.0) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=15000;")
        cursor.execute("PRAGMA foreign_keys=ON;")

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {USER_TABLE} (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                password TEXT,
                phone_number TEXT,
                email TEXT UNIQUE,
                student_id TEXT UNIQUE,
                rfid_tag TEXT UNIQUE,
                items_found INTEGER DEFAULT 0,
                items_find INTEGER DEFAULT 0,
                user_type TEXT DEFAULT 'both',
                reputation_score REAL DEFAULT 0,
                verification_status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
                id_number TEXT
            )
            """
        )

        cursor.execute(f"DROP TABLE IF EXISTS ""{CASE_TABLE}""")

        cursor.execute(f"DROP TABLE IF EXISTS {BOX_TABLE}")

        cursor.execute(f"DROP TABLE IF EXISTS {ITEM_TABLE}")
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {ITEM_TABLE} (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                image_url TEXT,
                finder_user_id INTEGER,
                finder_img_url TEXT,
                image_embedding TEXT,
                description_embedding TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (finder_user_id) REFERENCES {USER_TABLE} (user_id) ON DELETE SET NULL
            )
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {BOX_TABLE} (
                box_id INTEGER PRIMARY KEY AUTOINCREMENT,
                status INTEGER,
                location TEXT,
                load INTEGER,
                door_status INTEGER,
                last_accessed DATETIME
            )
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS "{CASE_TABLE}" (
                found_id INTEGER PRIMARY KEY AUTOINCREMENT,
                box_id INTEGER,
                reciver_image_url TEXT,
                reciver_id INTEGER,
                item_id INTEGER,
                status TEXT,
                case_close_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (box_id) REFERENCES {BOX_TABLE} (box_id) ON DELETE SET NULL,
                FOREIGN KEY (reciver_id) REFERENCES {USER_TABLE} (user_id) ON DELETE SET NULL,
                FOREIGN KEY (item_id) REFERENCES {ITEM_TABLE} (item_id) ON DELETE SET NULL
            )
            """
        )

        # Drop tables from the previous design if they still exist
        cursor.execute("DROP TABLE IF EXISTS FOUND_ITEMS")
        cursor.execute("DROP TABLE IF EXISTS COLLECTED_ITEMS")
        cursor.execute("DROP TABLE IF EXISTS FINDERS")
        cursor.execute("DROP TABLE IF EXISTS COLLECTORS")

        conn.commit()


@contextmanager
def get_db_connection():
    """Context manager that yields a SQLite connection with the proper pragmas."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=15.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=15000;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Helper conversion utilities
# ---------------------------------------------------------------------------
ITEM_WITH_CASE_SELECT = f"""
SELECT
    i.item_id,
    i.description,
    i.image_url,
    i.finder_user_id,
    i.finder_img_url,
    i.image_embedding,
    i.description_embedding,
    i.created_at AS item_created_at,
    c.found_id AS case_found_id,
    c.status AS case_status,
    c.reciver_id AS case_reciver_id,
    c.reciver_image_url AS case_reciver_image_url,
    c.case_close_at AS case_close_at,
    c.created_at AS case_created_at
FROM {ITEM_TABLE} AS i
LEFT JOIN "{CASE_TABLE}" AS c
    ON i.item_id = c.item_id
   AND c.found_id = (
        SELECT c2.found_id
        FROM "{CASE_TABLE}" AS c2
        WHERE c2.item_id = i.item_id
        ORDER BY datetime(c2.created_at) DESC, c2.found_id DESC
        LIMIT 1
    )
"""

ITEM_WITH_CASE_SUBQUERY = f"SELECT * FROM ({ITEM_WITH_CASE_SELECT}) AS item_case"


def _fetch_items(where_clause: str = "", params: Iterable[Any] = ()) -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = ITEM_WITH_CASE_SUBQUERY
        if where_clause:
            query = f"{query} {where_clause}"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()


def _row_to_item_dict(row: sqlite3.Row) -> Dict[str, Any]:
    status = row["case_status"] if row["case_status"] else "available"
    expires_at = row["case_close_at"]

    claimed_at: Optional[str]
    if status == "claimed" and expires_at:
        try:
            expires_dt = datetime.fromisoformat(expires_at)
            claimed_at = (expires_dt - timedelta(hours=1)).isoformat()
        except ValueError:
            claimed_at = None
    else:
        claimed_at = None

    return {
        "id": row["item_id"],
        "item_id": row["item_id"],
        "filename": row["image_url"],
        "image_url": row["image_url"],
        "description": row["description"],
        "status": status,
        "claimed_at": claimed_at,
        "claimed_by": row["case_reciver_id"],
        "expires_at": expires_at,
        "uploaded_at": row["item_created_at"],
        "image_embedding": row["image_embedding"],
        "description_embedding": row["description_embedding"],
        "finder_user_id": row["finder_user_id"],
        "finder_img_url": row["finder_img_url"],
    }


def _row_to_user_dict(row: sqlite3.Row) -> Dict[str, Any]:
    data = {
        "user_id": row["user_id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone_number"],
        "phone_number": row["phone_number"],
        "student_id": row["student_id"],
        "rfid_tag": row["rfid_tag"],
        "items_found": row["items_found"],
        "items_claimed": row["items_find"],
        "items_find": row["items_find"],
        "user_type": row["user_type"],
        "reputation_score": row["reputation_score"],
        "verification_status": row["verification_status"],
        "created_at": row["created_at"],
        "last_active": row["last_active"],
        "id_number": row["id_number"],
    }

    if row["rfid_tag"] and row["student_id"]:
        data["user_type"] = "both"
    elif row["rfid_tag"]:
        data["user_type"] = "finder"
    elif row["student_id"]:
        data["user_type"] = "collector"

    return data


def _row_to_finder_dict(row: sqlite3.Row) -> Dict[str, Any]:
    base = _row_to_user_dict(row)
    base.update(
        {
            "finder_id": row["user_id"],
        }
    )
    return base


def _row_to_collector_dict(row: sqlite3.Row) -> Dict[str, Any]:
    base = _row_to_user_dict(row)
    base.update(
        {
            "collector_id": row["user_id"],
        }
    )
    return base


# ---------------------------------------------------------------------------
# Item functions
# ---------------------------------------------------------------------------
def add_found_item(
    filename: str,
    image_embedding: Iterable[float],
    description: str = "",
    description_embedding: Optional[Iterable[float]] = None,
    finder_user_id: Optional[int] = None,
    finder_img_url: Optional[str] = None,
) -> int:
    """Insert a new item into the Item table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {ITEM_TABLE}
                (description, image_url, finder_user_id, finder_img_url, image_embedding, description_embedding)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                description,
                filename,
                finder_user_id,
                finder_img_url,
                json.dumps(list(image_embedding)) if image_embedding is not None else None,
                json.dumps(list(description_embedding)) if description_embedding is not None else None,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_available_items() -> List[Dict[str, Any]]:
    current_time = datetime.now().isoformat()
    rows = _fetch_items(
        "WHERE (case_status IS NULL OR case_status IN ('available', 'available_to_claim')) "
        "OR (case_status = 'claimed' AND case_close_at IS NOT NULL AND datetime(case_close_at) < datetime(?))",
        (current_time,),
    )
    return [_row_to_item_dict(row) for row in rows]


def get_all_items() -> List[Dict[str, Any]]:
    rows = _fetch_items("ORDER BY item_created_at DESC")
    return [_row_to_item_dict(row) for row in rows]


def claim_item(item_id: int, claimed_by_user_id: int) -> (bool, str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT found_id, status, case_close_at
            FROM "{CASE_TABLE}"
            WHERE item_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (item_id,),
        )
        case_row = cursor.fetchone()

        case_id: Optional[int]
        status: Optional[str]
        expires_at_str: Optional[str]

        if not case_row:
            cursor.execute(
                f"""
                INSERT INTO "{CASE_TABLE}" (item_id, status)
                VALUES (?, 'available')
                """,
                (item_id,),
            )
            case_id = cursor.lastrowid
            status = "available"
            expires_at_str = None
        else:
            case_id = case_row["found_id"]
            status = case_row["status"]
            expires_at_str = case_row["case_close_at"]

        if case_id is None:
            return False, "Item not found"

        if status == "claimed" and expires_at_str:
            try:
                expires_datetime = datetime.fromisoformat(expires_at_str)
            except ValueError:
                expires_datetime = None
            else:
                if expires_datetime and datetime.now() < expires_datetime:
                    return False, "Item is currently claimed"

        claimed_at = datetime.now()
        expires_at = claimed_at + timedelta(hours=1)
        cursor.execute(
            f"""
            UPDATE "{CASE_TABLE}"
            SET status = 'claimed', reciver_id = ?, case_close_at = ?
            WHERE found_id = ?
            """,
            (claimed_by_user_id, expires_at.isoformat(), case_id),
        )
        if cursor.rowcount == 0:
            return False, "Item not found"

        conn.commit()

    try:
        update_collector_stats(claimed_by_user_id, items_claimed_increment=1)
    except Exception as exc:  # pragma: no cover - best effort
        logging.warning("Failed to update collector stats: %s", exc)

    return True, "Item claimed successfully"


def release_expired_claims() -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        cursor.execute(
            f"""
            UPDATE "{CASE_TABLE}"
            SET status = 'available_to_claim', reciver_id = NULL, case_close_at = NULL
            WHERE status = 'claimed' AND case_close_at IS NOT NULL AND datetime(case_close_at) < datetime(?)
            """,
            (current_time,),
        )
        conn.commit()
        return cursor.rowcount


def delete_item(filename: str) -> bool:
    rows = _fetch_items("WHERE image_url = ?", (filename,))
    if not rows:
        return False

    item_id = rows[0]["item_id"]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM \"{CASE_TABLE}\" WHERE item_id = ?",
            (item_id,),
        )
        cursor.execute(
            f"DELETE FROM {ITEM_TABLE} WHERE item_id = ?",
            (item_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_item_by_filename(filename: str) -> Optional[Dict[str, Any]]:
    rows = _fetch_items("WHERE image_url = ?", (filename,))
    return _row_to_item_dict(rows[0]) if rows else None


def search_items(query_embedding: Iterable[float], threshold: float = 0.4) -> List[Dict[str, Any]]:
    current_time = datetime.now().isoformat()
    items = _fetch_items(
        "WHERE (case_status IS NULL OR case_status IN ('available', 'available_to_claim')) "
        "OR (case_status = 'claimed' AND case_close_at IS NOT NULL AND datetime(case_close_at) < datetime(?))",
        (current_time,),
    )

    query_emb = np.array(list(query_embedding), dtype=np.float32)
    results: List[Dict[str, Any]] = []

    for item in items:
        item_dict = _row_to_item_dict(item)
        img_emb_raw = item_dict["image_embedding"]
        if not img_emb_raw:
            continue

        img_emb = np.array(json.loads(img_emb_raw), dtype=np.float32)
        img_score = float(
            np.dot(query_emb, img_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(img_emb))
        )

        desc_score = 0.0
        if item_dict["description_embedding"]:
            desc_emb = np.array(json.loads(item_dict["description_embedding"]), dtype=np.float32)
            desc_score = float(
                np.dot(query_emb, desc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(desc_emb))
            )

        final_score = 0.6 * desc_score + 0.4 * img_score
        if final_score > threshold:
            if item_dict["status"] == "claimed" and item_dict["expires_at"]:
                expires_datetime = datetime.fromisoformat(item_dict["expires_at"])
                if datetime.now() > expires_datetime:
                    release_expired_claims()
                    item_dict["status"] = "available"
            results.append(
                {
                    "id": item_dict["id"],
                    "filename": item_dict["filename"],
                    "description": item_dict["description"],
                    "score": final_score,
                    "status": item_dict["status"],
                    "claimed_by": item_dict["claimed_by"],
                    "expires_at": item_dict["expires_at"],
                    "uploaded_at": item_dict["uploaded_at"],
                }
            )

    return results


# ---------------------------------------------------------------------------
# Collecting helpers
# ---------------------------------------------------------------------------
def collect_found_item(
    filename: str,
    imgtaken_timestamp: float,
    box_id: Optional[int],
    finder_id: Optional[int] = None,
) -> int:
    """Register a collected item and associate it with a case."""
    collected_iso = datetime.fromtimestamp(imgtaken_timestamp).isoformat()

    box_id_value: Optional[int]
    if box_id is None or box_id == "":
        box_id_value = None
    else:
        try:
            box_id_value = int(box_id)
        except (TypeError, ValueError):
            box_id_value = None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {ITEM_TABLE} (description, image_url, finder_user_id, finder_img_url, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("", filename, finder_id, filename, collected_iso),
        )
        item_id = cursor.lastrowid

        cursor.execute(
            f"""
            INSERT INTO "{CASE_TABLE}" (box_id, item_id, status, created_at, reciver_image_url, reciver_id, case_close_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                box_id_value,
                item_id,
                "collected",
                collected_iso,
                None,
                None,
                None,
            ),
        )

        if finder_id:
            cursor.execute(
                f"""
                UPDATE {USER_TABLE}
                SET items_found = items_found + 1
                WHERE user_id = ?
                """,
                (finder_id,),
            )

        conn.commit()

    return item_id


def get_collected_items() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT c.found_id, c.box_id, c.created_at,
                   i.image_url, i.item_id
            FROM "{CASE_TABLE}" AS c
            LEFT JOIN {ITEM_TABLE} AS i ON c.item_id = i.item_id
            ORDER BY c.created_at DESC
            """
        )
        rows = cursor.fetchall()

    collected: List[Dict[str, Any]] = []
    for row in rows:
        collected_timestamp = None
        if row["created_at"]:
            try:
                collected_timestamp = datetime.fromisoformat(row["created_at"]).timestamp()
            except ValueError:
                collected_timestamp = None

        collected.append(
            {
                "id": row["found_id"],
                "case_id": row["found_id"],
                "box_id": row["box_id"],
                "filename": row["image_url"],
                "item_id": row["item_id"],
                "imgtaken_timestamp": collected_timestamp,
                "uploaded_at": row["created_at"],
            }
        )
    return collected


def clear_all_items() -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM \"{CASE_TABLE}\"")
        cursor.execute(f"DELETE FROM {ITEM_TABLE}")
        conn.commit()
        return cursor.rowcount


# ---------------------------------------------------------------------------
# User management functions
# ---------------------------------------------------------------------------
def add_user(
    name: str,
    email: Optional[str] = None,
    phone_number: Optional[str] = None,
    rfid_tag: Optional[str] = None,
    student_id: Optional[str] = None,
    user_type: str = "both",
    password: Optional[str] = None,
    id_number: Optional[str] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now_iso = datetime.now().isoformat()
        cursor.execute(
            f"""
            INSERT INTO {USER_TABLE}
                (name, password, phone_number, email, student_id, rfid_tag, user_type,
                 created_at, last_active, id_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, password, phone_number, email, student_id, rfid_tag, user_type, now_iso, now_iso, id_number),
        )
        conn.commit()
        return cursor.lastrowid


def add_finder(name: str, email: Optional[str] = None, phone: Optional[str] = None, rfid_tag: Optional[str] = None) -> int:
    return add_user(name, email, phone, rfid_tag=rfid_tag, user_type="finder")


def add_collector(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    student_id: Optional[str] = None,
    id_number: Optional[str] = None,
) -> int:
    return add_user(name, email, phone_number=phone, student_id=student_id, user_type="collector", id_number=id_number)


def _fetch_single_user(query: str, params: Iterable[Any]) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        row = cursor.fetchone()
        return _row_to_user_dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    return _fetch_single_user(f"SELECT * FROM {USER_TABLE} WHERE user_id = ?", (user_id,))


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return _fetch_single_user(f"SELECT * FROM {USER_TABLE} WHERE email = ?", (email,))


def get_user_by_rfid(rfid_tag: str) -> Optional[Dict[str, Any]]:
    return _fetch_single_user(f"SELECT * FROM {USER_TABLE} WHERE rfid_tag = ?", (rfid_tag,))


def get_user_by_student_id(student_id: str) -> Optional[Dict[str, Any]]:
    return _fetch_single_user(f"SELECT * FROM {USER_TABLE} WHERE student_id = ?", (student_id,))


def get_finder_by_id(finder_id: int) -> Optional[Dict[str, Any]]:
    user = get_user_by_id(finder_id)
    return _convert_to_finder(user)


def get_finder_by_email(email: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_email(email)
    return _convert_to_finder(user)


def get_finder_by_rfid(rfid_tag: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_rfid(rfid_tag)
    return _convert_to_finder(user)


def _convert_to_finder(user: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not user:
        return None
    user = dict(user)
    user.setdefault("finder_id", user.get("user_id"))
    return user


def get_collector_by_id(collector_id: int) -> Optional[Dict[str, Any]]:
    user = get_user_by_id(collector_id)
    return _convert_to_collector(user)


def get_collector_by_email(email: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_email(email)
    return _convert_to_collector(user)


def get_collector_by_student_id(student_id: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_student_id(student_id)
    return _convert_to_collector(user)


def _convert_to_collector(user: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not user:
        return None
    user = dict(user)
    user.setdefault("collector_id", user.get("user_id"))
    return user


def get_all_finders() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM {USER_TABLE} WHERE rfid_tag IS NOT NULL OR user_type IN ('finder', 'both') ORDER BY created_at DESC"
        )
        return [_row_to_finder_dict(row) for row in cursor.fetchall()]


def get_all_collectors() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM {USER_TABLE} WHERE student_id IS NOT NULL OR user_type IN ('collector', 'both') ORDER BY created_at DESC"
        )
        return [_row_to_collector_dict(row) for row in cursor.fetchall()]


def get_all_users() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {USER_TABLE} ORDER BY created_at DESC")
        return [_row_to_user_dict(row) for row in cursor.fetchall()]


def update_user_stats(
    user_id: int,
    items_found_increment: int = 0,
    items_claimed_increment: int = 0,
) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {USER_TABLE}
            SET items_found = items_found + ?,
                items_find = items_find + ?,
                last_active = ?
            WHERE user_id = ?
            """,
            (items_found_increment, items_claimed_increment, datetime.now().isoformat(), user_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_finder_stats(
    finder_id: int,
    items_found_increment: int = 0,
    reputation_increment: float = 0,
) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {USER_TABLE}
            SET items_found = items_found + ?,
                reputation_score = reputation_score + ?,
                last_active = ?
            WHERE user_id = ?
            """,
            (items_found_increment, reputation_increment, datetime.now().isoformat(), finder_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_collector_stats(
    collector_id: int,
    items_claimed_increment: int = 0,
    verification_status: Optional[str] = None,
) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        fields = ["items_find = items_find + ?", "last_active = ?"]
        params: List[Any] = [items_claimed_increment, datetime.now().isoformat()]

        if verification_status is not None:
            fields.append("verification_status = ?")
            params.append(verification_status)

        params.append(collector_id)
        cursor.execute(
            f"UPDATE {USER_TABLE} SET {', '.join(fields)} WHERE user_id = ?",
            tuple(params),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_user_last_active(user_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {USER_TABLE} SET last_active = ? WHERE user_id = ?",
            (datetime.now().isoformat(), user_id),
        )
        conn.commit()
        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Box helpers
# ---------------------------------------------------------------------------
def add_box(location: str, status: bool = True, door_status: bool = False, load: int = 0) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {BOX_TABLE} (status, location, load, door_status, last_accessed)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                1 if status else 0,
                location,
                load,
                1 if door_status else 0,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def update_box(
    box_id: int,
    status: Optional[bool] = None,
    door_status: Optional[bool] = None,
    location: Optional[str] = None,
    load: Optional[int] = None,
) -> int:
    fields: List[str] = []
    values: List[Any] = []

    if status is not None:
        fields.append("status = ?")
        values.append(1 if status else 0)
    if door_status is not None:
        fields.append("door_status = ?")
        values.append(1 if door_status else 0)
    if location is not None:
        fields.append("location = ?")
        values.append(location)
    if load is not None:
        fields.append("load = ?")
        values.append(load)
    fields.append("last_accessed = ?")
    values.append(datetime.now().isoformat())

    if not fields:
        return 0

    values.append(box_id)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {BOX_TABLE} SET {', '.join(fields)} WHERE box_id = ?",
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount


def delete_box(box_id: int) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {BOX_TABLE} WHERE box_id = ?", (box_id,))
        conn.commit()
        return cursor.rowcount


def get_box_status(box_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {BOX_TABLE} WHERE box_id = ?", (box_id,))
        row = cursor.fetchone()
    if not row:
        return None
    return {
        "box_id": row["box_id"],
        "status": bool(row["status"]),
        "door_status": bool(row["door_status"]),
        "location": row["location"],
        "load": row["load"],
        "last_accessed": row["last_accessed"],
    }


def update_box_status(
    box_id: int,
    status: Optional[str] = None,
    current_load: Optional[int] = None,
    door_status: Optional[str] = None,
) -> int:
    bool_map = {
        "open": True,
        "closed": False,
        True: True,
        False: False,
        "1": True,
        "0": False,
        "available": True,
        "collect_request": False,
        "occupied": False,
    }

    status_bool = None
    if status is not None:
        status_bool = bool_map.get(status, status)

    door_bool = None
    if door_status is not None:
        door_bool = bool_map.get(door_status, door_status)

    return update_box(
        box_id,
        status=status_bool if isinstance(status_bool, bool) else None,
        door_status=door_bool if isinstance(door_bool, bool) else None,
        load=current_load,
    )


def get_all_boxes() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {BOX_TABLE} ORDER BY box_id")
        rows = cursor.fetchall()
    return [
        {
            "box_id": row["box_id"],
            "status": bool(row["status"]),
            "door_status": bool(row["door_status"]),
            "location": row["location"],
            "load": row["load"],
            "last_accessed": row["last_accessed"],
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Case helpers
# ---------------------------------------------------------------------------
def add_case(
    box_id: int,
    receiver_id: Optional[int] = None,
    receiver_image_url: Optional[str] = None,
    item_id: Optional[int] = None,
    status: str = "available",
    case_close_at: Optional[str] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO "{CASE_TABLE}" (box_id, reciver_image_url, reciver_id, item_id, status, case_close_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                box_id,
                receiver_image_url,
                receiver_id,
                item_id,
                status,
                case_close_at,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def update_case(
    found_id: Optional[int] = None,
    *,
    case_id: Optional[int] = None,
    box_id: Optional[int] = None,
    receiver_id: Optional[int] = None,
    receiver_image_url: Optional[str] = None,
    item_id: Optional[int] = None,
    status: Optional[str] = None,
    case_close_at: Optional[str] = None,
) -> int:
    if found_id is None:
        found_id = case_id

    if found_id is None:
        return 0

    fields: List[str] = []
    values: List[Any] = []

    if box_id is not None:
        fields.append("box_id = ?")
        values.append(box_id)
    if receiver_id is not None:
        fields.append("reciver_id = ?")
        values.append(receiver_id)
    if receiver_image_url is not None:
        fields.append("reciver_image_url = ?")
        values.append(receiver_image_url)
    if item_id is not None:
        fields.append("item_id = ?")
        values.append(item_id)
    if status is not None:
        fields.append("status = ?")
        values.append(status)
    if case_close_at is not None:
        fields.append("case_close_at = ?")
        values.append(case_close_at)

    if not fields:
        return 0

    values.append(found_id)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE \"{CASE_TABLE}\" SET {', '.join(fields)} WHERE found_id = ?",
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount


def delete_case(case_id: int) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM \"{CASE_TABLE}\" WHERE found_id = ?", (case_id,))
        conn.commit()
        return cursor.rowcount


def get_case(case_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM \"{CASE_TABLE}\" WHERE found_id = ?", (case_id,))
        row = cursor.fetchone()
    if not row:
        return None
    return {
        "found_id": row["found_id"],
        "box_id": row["box_id"],
        "receiver_image_url": row["reciver_image_url"],
        "receiver_id": row["reciver_id"],
        "item_id": row["item_id"],
        "status": row["status"],
        "case_close_at": row["case_close_at"],
        "created_at": row["created_at"],
    }


def get_all_case() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM \"{CASE_TABLE}\" ORDER BY found_id")
        rows = cursor.fetchall()
    return [
        {
            "found_id": row["found_id"],
            "box_id": row["box_id"],
            "receiver_image_url": row["reciver_image_url"],
            "receiver_id": row["reciver_id"],
            "item_id": row["item_id"],
            "status": row["status"],
            "case_close_at": row["case_close_at"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


# Ensure tables exist when the module is imported in CLI utilities
init_database()

if __name__ == "__main__":  # pragma: no cover
    init_database()
