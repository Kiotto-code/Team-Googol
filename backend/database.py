import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Iterator, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lost_and_found.db")

_schema_initialized = False


def _apply_connection_pragmas(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=15000;")
    conn.execute("PRAGMA foreign_keys=ON;")


def _add_column_if_missing(cursor: sqlite3.Cursor, table: str, column: str, definition: str) -> None:
    cursor.execute(f"PRAGMA table_info({table})")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if column not in existing_columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _ensure_user_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS User (
            user_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL,
            password     TEXT,
            phone_number INTEGER,
            email        TEXT UNIQUE,
            student_id   INTEGER,
            rfid_tag     TEXT UNIQUE,
            items_found  INTEGER DEFAULT 0,
            items_find   INTEGER DEFAULT 0,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    _add_column_if_missing(cursor, "User", "items_claimed", "INTEGER DEFAULT 0")
    _add_column_if_missing(cursor, "User", "user_type", "TEXT DEFAULT 'both'")
    _add_column_if_missing(cursor, "User", "reputation_score", "REAL DEFAULT 0")
    _add_column_if_missing(cursor, "User", "verification_status", "TEXT DEFAULT 'unverified'")
    _add_column_if_missing(cursor, "User", "id_number", "TEXT")
    _add_column_if_missing(cursor, "User", "last_active", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")


def _ensure_item_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Item (
            item_id               INTEGER PRIMARY KEY AUTOINCREMENT,
            description           TEXT,
            image_url             TEXT,
            image_embedding       TEXT,
            description_embedding TEXT,
            status                TEXT,
            finder_user_id        INTEGER,
            finder_img_url        TEXT,
            created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (finder_user_id) REFERENCES User(user_id)
        )
        """
    )

    _add_column_if_missing(cursor, "Item", "claimed_by_user_id", "INTEGER")
    _add_column_if_missing(cursor, "Item", "claimed_at", "TIMESTAMP")
    _add_column_if_missing(cursor, "Item", "expires_at", "TIMESTAMP")


def _ensure_box_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Box (
            box_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            status        INTEGER,
            location      TEXT,
            load          INTEGER,
            door_status   INTEGER,
            last_accessed TIMESTAMP
        )
        """
    )

    _add_column_if_missing(cursor, "Box", "capacity", "INTEGER DEFAULT 1")
    _add_column_if_missing(cursor, "Box", "last_updated", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")


def _ensure_case_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Case (
            found_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            box_id            INTEGER,
            reciver_image_url TEXT,
            reciver_id        INTEGER,
            item_id           INTEGER,
            status            TEXT,
            case_close_at     TIMESTAMP,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (box_id) REFERENCES Box(box_id),
            FOREIGN KEY (reciver_id) REFERENCES User(user_id),
            FOREIGN KEY (item_id) REFERENCES Item(item_id)
        )
        """
    )

    _add_column_if_missing(cursor, "Case", "collector_image_url", "TEXT")
    _add_column_if_missing(cursor, "Case", "collector_timestamp", "REAL")
    _add_column_if_missing(cursor, "Case", "finder_user_id", "INTEGER")
    _add_column_if_missing(cursor, "Case", "receiver_image_url", "TEXT")
    _add_column_if_missing(cursor, "Case", "receiver_id", "INTEGER")


def _ensure_schema(conn: sqlite3.Connection) -> None:
    global _schema_initialized
    if _schema_initialized:
        return
    cursor = conn.cursor()
    _ensure_user_table(cursor)
    _ensure_item_table(cursor)
    _ensure_box_table(cursor)
    _ensure_case_table(cursor)
    conn.commit()
    _schema_initialized = True


@contextmanager
def get_db_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DATABASE_PATH, timeout=15.0)
    try:
        conn.row_factory = sqlite3.Row
        _apply_connection_pragmas(conn)
        _ensure_schema(conn)
        yield conn
    finally:
        conn.close()


def init_database() -> None:
    with sqlite3.connect(DATABASE_PATH, timeout=15.0) as conn:
        conn.row_factory = sqlite3.Row
        _apply_connection_pragmas(conn)
        _ensure_schema(conn)


# ---------------------------------------------------------------------------
# Item helpers
# ---------------------------------------------------------------------------

def _normalize_item_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["item_id"],
        "filename": row["image_url"],
        "description": row["description"],
        "status": row["status"],
        "claimed_by": row["claimed_by_user_id"],
        "claimed_at": row["claimed_at"],
        "expires_at": row["expires_at"],
        "uploaded_at": row["created_at"],
    }


def add_found_item(
    filename: str,
    image_embedding: List[float],
    description: str = "",
    description_embedding: Optional[List[float]] = None,
) -> int:
    """Insert a new item into the Item table using the new schema."""
    img_emb_json = json.dumps(image_embedding)
    desc_emb_json = json.dumps(description_embedding) if description_embedding else None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Item (
                description,
                image_url,
                image_embedding,
                description_embedding,
                status
            )
            VALUES (?, ?, ?, ?, 'available')
            """,
            (description, filename, img_emb_json, desc_emb_json),
        )
        conn.commit()
        return cursor.lastrowid


def get_available_items() -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = datetime.utcnow().isoformat()
        cursor.execute(
            """
            SELECT
                item_id,
                image_url,
                description,
                status,
                claimed_by_user_id,
                claimed_at,
                expires_at,
                created_at
            FROM Item
            WHERE status = 'available'
               OR (status = 'claimed' AND expires_at IS NOT NULL AND datetime(expires_at) < datetime(?))
            ORDER BY created_at DESC
            """,
            (current_time,),
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row["item_id"],
                "filename": row["image_url"],
                "description": row["description"],
                "status": row["status"],
                "claimed_by": row["claimed_by_user_id"],
                "claimed_at": row["claimed_at"],
                "expires_at": row["expires_at"],
                "uploaded_at": row["created_at"],
            }
            for row in rows
        ]


def get_all_items() -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                item_id,
                image_url,
                description,
                status,
                claimed_by_user_id,
                claimed_at,
                expires_at,
                created_at
            FROM Item
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row["item_id"],
                "filename": row["image_url"],
                "description": row["description"],
                "status": row["status"],
                "claimed_by": row["claimed_by_user_id"],
                "claimed_at": row["claimed_at"],
                "expires_at": row["expires_at"],
                "uploaded_at": row["created_at"],
            }
            for row in rows
        ]


def get_item_by_filename(filename: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                item_id,
                image_url,
                description,
                status,
                claimed_by_user_id,
                claimed_at,
                expires_at,
                created_at
            FROM Item
            WHERE image_url = ?
            """,
            (filename,),
        )
        row = cursor.fetchone()
        return _normalize_item_row(row) if row else None


def delete_item(filename: str) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Item WHERE image_url = ?", (filename,))
        conn.commit()
        return cursor.rowcount > 0


def clear_all_items() -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Item")
        conn.commit()
        return cursor.rowcount


def claim_item(item_id: int, claimed_by_collector_id: int) -> Tuple[bool, str]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, expires_at FROM Item WHERE item_id = ?",
            (item_id,),
        )
        row = cursor.fetchone()
        if not row:
            return False, "Item not found"

        status = row["status"]
        expires_at = row["expires_at"]
        if status == "claimed" and expires_at:
            expires_datetime = datetime.fromisoformat(expires_at)
            if datetime.utcnow() < expires_datetime:
                return False, "Item is currently claimed"

        claimed_at = datetime.utcnow()
        new_expiry = claimed_at + timedelta(hours=1)
        cursor.execute(
            """
            UPDATE Item
               SET status = 'claimed',
                   claimed_at = ?,
                   claimed_by_user_id = ?,
                   expires_at = ?
             WHERE item_id = ?
            """,
            (
                claimed_at.isoformat(),
                claimed_by_collector_id,
                new_expiry.isoformat(),
                item_id,
            ),
        )
        conn.commit()

    update_user_stats(claimed_by_collector_id, items_claimed_increment=1)
    return True, "Item claimed successfully"


def release_expired_claims() -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = datetime.utcnow().isoformat()
        cursor.execute(
            """
            UPDATE Item
               SET status = 'available',
                   claimed_at = NULL,
                   claimed_by_user_id = NULL,
                   expires_at = NULL
             WHERE status = 'claimed'
               AND expires_at IS NOT NULL
               AND datetime(expires_at) < datetime(?)
            """,
            (current_time,),
        )
        conn.commit()
        return cursor.rowcount


def search_items(query_embedding: List[float], threshold: float = 0.4) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = datetime.utcnow().isoformat()
        cursor.execute(
            """
            SELECT
                item_id,
                image_url,
                description,
                image_embedding,
                description_embedding,
                status,
                claimed_by_user_id,
                expires_at,
                created_at
            FROM Item
            WHERE status = 'available'
               OR (status = 'claimed' AND expires_at IS NOT NULL AND datetime(expires_at) < datetime(?))
            """,
            (current_time,),
        )
        items = cursor.fetchall()

    import numpy as np

    query_emb = np.array(query_embedding, dtype=np.float32)
    results: List[Dict[str, Any]] = []
    for item in items:
        img_emb = json.loads(item["image_embedding"])
        img_emb = np.array(img_emb, dtype=np.float32)
        if np.linalg.norm(img_emb) == 0 or np.linalg.norm(query_emb) == 0:
            continue
        img_score = float(np.dot(query_emb, img_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(img_emb)))

        desc_score = 0.0
        if item["description_embedding"]:
            desc_emb = np.array(json.loads(item["description_embedding"]), dtype=np.float32)
            if np.linalg.norm(desc_emb) != 0:
                desc_score = float(
                    np.dot(query_emb, desc_emb)
                    / (np.linalg.norm(query_emb) * np.linalg.norm(desc_emb))
                )

        final_score = 0.6 * desc_score + 0.4 * img_score
        if final_score > threshold:
            status = item["status"]
            expires_at = item["expires_at"]
            if status == "claimed" and expires_at:
                expires_datetime = datetime.fromisoformat(expires_at)
                if datetime.utcnow() > expires_datetime:
                    status = "available"
            results.append(
                {
                    "id": item["item_id"],
                    "filename": item["image_url"],
                    "description": item["description"],
                    "score": final_score,
                    "status": status,
                    "claimed_by": item["claimed_by_user_id"],
                    "expires_at": item["expires_at"],
                    "uploaded_at": item["created_at"],
                }
            )

    return results


# ---------------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------------

def _normalize_user_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone_number"],
        "phone_number": row["phone_number"],
        "rfid_tag": row["rfid_tag"],
        "student_id": row["student_id"],
        "items_found": row["items_found"],
        "items_claimed": row["items_claimed"],
        "reputation_score": row["reputation_score"],
        "verification_status": row["verification_status"],
        "id_number": row["id_number"],
        "user_type": row["user_type"],
        "created_at": row["created_at"],
        "last_active": row["last_active"],
    }


def add_user(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    rfid_tag: Optional[str] = None,
    student_id: Optional[str] = None,
    user_type: str = "both",
    password: Optional[str] = None,
    id_number: Optional[str] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute(
            """
            INSERT INTO User (
                name,
                email,
                phone_number,
                rfid_tag,
                student_id,
                user_type,
                password,
                id_number,
                created_at,
                last_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, email, phone, rfid_tag, student_id, user_type, password, id_number, now, now),
        )
        conn.commit()
        return cursor.lastrowid


def add_finder(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    rfid_tag: Optional[str] = None,
) -> int:
    return add_user(name, email, phone, rfid_tag, None, user_type="finder")


def add_collector(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    student_id: Optional[str] = None,
    id_number: Optional[str] = None,
) -> int:
    return add_user(name, email, phone, None, student_id, user_type="collector", id_number=id_number)


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return _normalize_user_row(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE email = ?", (email,))
        row = cursor.fetchone()
        return _normalize_user_row(row) if row else None


def get_user_by_rfid(rfid_tag: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE rfid_tag = ?", (rfid_tag,))
        row = cursor.fetchone()
        return _normalize_user_row(row) if row else None


def get_user_by_student_id(student_id: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        return _normalize_user_row(row) if row else None


def _finder_projection(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "finder_id": row["user_id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "rfid_tag": row["rfid_tag"],
        "items_found": row["items_found"],
        "reputation_score": row["reputation_score"],
        "created_at": row["created_at"],
        "last_active": row["last_active"],
        "user_type": row["user_type"],
    }


def _collector_projection(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "collector_id": row["user_id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "student_id": row["student_id"],
        "id_number": row["id_number"],
        "items_claimed": row["items_claimed"],
        "verification_status": row["verification_status"],
        "created_at": row["created_at"],
        "last_active": row["last_active"],
        "user_type": row["user_type"],
    }


def get_finder_by_id(finder_id: int) -> Optional[Dict[str, Any]]:
    user = get_user_by_id(finder_id)
    if user and user["user_type"] in {"finder", "both"}:
        return _finder_projection(user)
    return None


def get_finder_by_email(email: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_email(email)
    if user and user["user_type"] in {"finder", "both"}:
        return _finder_projection(user)
    return None


def get_finder_by_rfid(rfid_tag: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_rfid(rfid_tag)
    if user and user["user_type"] in {"finder", "both"}:
        return _finder_projection(user)
    return None


def get_collector_by_id(collector_id: int) -> Optional[Dict[str, Any]]:
    user = get_user_by_id(collector_id)
    if user and user["user_type"] in {"collector", "both"}:
        return _collector_projection(user)
    return None


def get_collector_by_email(email: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_email(email)
    if user and user["user_type"] in {"collector", "both"}:
        return _collector_projection(user)
    return None


def get_collector_by_student_id(student_id: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_student_id(student_id)
    if user and user["user_type"] in {"collector", "both"}:
        return _collector_projection(user)
    return None


def get_all_finders() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE user_type IN ('finder', 'both') ORDER BY created_at DESC")
        return [_finder_projection(_normalize_user_row(row)) for row in cursor.fetchall()]


def get_all_collectors() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE user_type IN ('collector', 'both') ORDER BY created_at DESC")
        return [_collector_projection(_normalize_user_row(row)) for row in cursor.fetchall()]


def get_all_users() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User ORDER BY created_at DESC")
        return [_normalize_user_row(row) for row in cursor.fetchall()]


def update_user_stats(
    user_id: int,
    items_found_increment: int = 0,
    items_claimed_increment: int = 0,
    reputation_increment: float = 0.0,
    verification_status: Optional[str] = None,
) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        updates = ["last_active = ?", "items_found = items_found + ?", "items_claimed = items_claimed + ?", "items_find = items_find + ?", "reputation_score = reputation_score + ?"]
        params: List[Any] = [
            datetime.utcnow().isoformat(),
            items_found_increment,
            items_claimed_increment,
            items_claimed_increment,
            reputation_increment,
        ]
        if verification_status is not None:
            updates.append("verification_status = ?")
            params.append(verification_status)

        params.append(user_id)
        cursor.execute(
            f"""
            UPDATE User
               SET {', '.join(updates)}
             WHERE user_id = ?
            """,
            params,
        )
        conn.commit()
        return cursor.rowcount > 0


def update_finder_stats(
    finder_id: int,
    items_found_increment: int = 0,
    reputation_increment: float = 0.0,
) -> bool:
    return update_user_stats(
        finder_id,
        items_found_increment=items_found_increment,
        reputation_increment=reputation_increment,
    )


def update_collector_stats(
    collector_id: int,
    items_claimed_increment: int = 0,
    verification_status: Optional[str] = None,
) -> bool:
    return update_user_stats(
        collector_id,
        items_claimed_increment=items_claimed_increment,
        verification_status=verification_status,
    )


def update_user_last_active(user_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE User SET last_active = ? WHERE user_id = ?",
            (datetime.utcnow().isoformat(), user_id),
        )
        conn.commit()
        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Box helpers
# ---------------------------------------------------------------------------

def add_box(
    location: str,
    status: Any = True,
    door_status: Any = False,
    load: int = 0,
    capacity: int = 1,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        status_value = status if isinstance(status, str) else ("available" if status else "unavailable")
        door_value = 1 if bool(door_status) else 0
        cursor.execute(
            """
            INSERT INTO Box (status, location, load, door_status, capacity, last_accessed, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (status_value, location, load, door_value, capacity, now, now),
        )
        conn.commit()
        return cursor.lastrowid


def update_box(
    box_id: Any,
    status: Optional[Any] = None,
    door_status: Optional[Any] = None,
    location: Optional[str] = None,
    load: Optional[int] = None,
    capacity: Optional[int] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        fields: List[str] = []
        values: List[Any] = []

        if status is not None:
            status_value = status if isinstance(status, str) else ("available" if status else "unavailable")
            fields.append("status = ?")
            values.append(status_value)
        if door_status is not None:
            fields.append("door_status = ?")
            values.append(1 if bool(door_status) else 0)
        if location is not None:
            fields.append("location = ?")
            values.append(location)
        if load is not None:
            fields.append("load = ?")
            values.append(load)
        if capacity is not None:
            fields.append("capacity = ?")
            values.append(capacity)

        if not fields:
            return 0

        fields.append("last_accessed = ?")
        fields.append("last_updated = ?")
        now = datetime.utcnow().isoformat()
        values.extend([now, now, box_id])

        cursor.execute(
            f"UPDATE Box SET {', '.join(fields)} WHERE box_id = ?",
            values,
        )
        conn.commit()
        return cursor.rowcount


def get_box_status(box_id: Any) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                box_id,
                status,
                location,
                load,
                load AS current_load,
                door_status,
                last_accessed,
                capacity,
                last_updated
            FROM Box
            WHERE box_id = ?
            """,
            (box_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "box_id": row["box_id"],
            "status": row["status"],
            "location": row["location"],
            "load": row["load"],
            "current_load": row["current_load"],
            "door_status": bool(row["door_status"]),
            "last_accessed": row["last_accessed"],
            "capacity": row["capacity"],
            "last_updated": row["last_updated"],
        }


def update_box_status(
    box_id: Any,
    status: Optional[Any] = None,
    current_load: Optional[int] = None,
    door_status: Optional[Any] = None,
    capacity: Optional[int] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        fields: List[str] = []
        values: List[Any] = []

        if status is not None:
            status_value = status if isinstance(status, str) else ("available" if status else "unavailable")
            fields.append("status = ?")
            values.append(status_value)
        if current_load is not None:
            fields.append("load = ?")
            values.append(current_load)
        if door_status is not None:
            fields.append("door_status = ?")
            values.append(1 if bool(door_status) else 0)
        if capacity is not None:
            fields.append("capacity = ?")
            values.append(capacity)

        if not fields:
            return 0

        now = datetime.utcnow().isoformat()
        fields.append("last_updated = ?")
        values.append(now)

        cursor.execute(
            f"UPDATE Box SET {', '.join(fields)} WHERE box_id = ?",
            (*values, box_id),
        )
        conn.commit()
        return cursor.rowcount


def get_all_boxes() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                box_id,
                status,
                location,
                load,
                door_status,
                last_accessed,
                capacity,
                last_updated
            FROM Box
            ORDER BY box_id
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "box_id": row["box_id"],
                "status": row["status"],
                "location": row["location"],
                "load": row["load"],
                "door_status": bool(row["door_status"]),
                "last_accessed": row["last_accessed"],
                "capacity": row["capacity"],
                "last_updated": row["last_updated"],
            }
            for row in rows
        ]


def delete_box(box_id: Any) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Box WHERE box_id = ?", (box_id,))
        conn.commit()
        return cursor.rowcount


# ---------------------------------------------------------------------------
# Case helpers
# ---------------------------------------------------------------------------

def add_case(
    box_id: Any,
    receiver_id: Optional[int] = None,
    receiver_image_url: Optional[str] = None,
    item_id: Optional[int] = None,
    status: str = "available",
    case_close_at: Optional[str] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute(
            """
            INSERT INTO Case (
                box_id,
                reciver_image_url,
                reciver_id,
                item_id,
                status,
                case_close_at,
                created_at,
                receiver_image_url,
                receiver_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                box_id,
                receiver_image_url,
                receiver_id,
                item_id,
                status,
                case_close_at,
                now,
                receiver_image_url,
                receiver_id,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def update_case(
    found_id: Any,
    box_id: Optional[Any] = None,
    receiver_id: Optional[int] = None,
    receiver_image_url: Optional[str] = None,
    item_id: Optional[int] = None,
    status: Optional[str] = None,
    case_close_at: Optional[str] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        fields: List[str] = []
        values: List[Any] = []

        if box_id is not None:
            fields.append("box_id = ?")
            values.append(box_id)
        if receiver_id is not None:
            fields.append("reciver_id = ?")
            fields.append("receiver_id = ?")
            values.extend([receiver_id, receiver_id])
        if receiver_image_url is not None:
            fields.append("reciver_image_url = ?")
            fields.append("receiver_image_url = ?")
            values.extend([receiver_image_url, receiver_image_url])
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
        cursor.execute(
            f"UPDATE Case SET {', '.join(fields)} WHERE found_id = ?",
            values,
        )
        conn.commit()
        return cursor.rowcount


def delete_case(case_id: Any) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Case WHERE found_id = ?", (case_id,))
        conn.commit()
        return cursor.rowcount


def get_case(case_id: Any) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Case WHERE found_id = ?", (case_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return dict(row)


def get_all_case() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Case ORDER BY found_id")
        return [dict(row) for row in cursor.fetchall()]


def collect_found_item(
    filename: str,
    imgtaken_timestamp: float,
    box_id: Any,
    finder_id: Optional[int] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute(
            """
            INSERT INTO Case (
                box_id,
                reciver_image_url,
                reciver_id,
                status,
                created_at,
                collector_image_url,
                collector_timestamp,
                finder_user_id,
                receiver_image_url,
                receiver_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                box_id,
                filename,
                finder_id,
                "collected",
                now,
                filename,
                imgtaken_timestamp,
                finder_id,
                filename,
                finder_id,
            ),
        )
        conn.commit()
        case_id = cursor.lastrowid

    if finder_id:
        update_finder_stats(finder_id, items_found_increment=1)
    return case_id


def get_collected_items() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                found_id,
                box_id,
                collector_image_url,
                collector_timestamp,
                created_at,
                finder_user_id
            FROM Case
            WHERE collector_image_url IS NOT NULL
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row["found_id"],
                "box_id": row["box_id"],
                "filename": row["collector_image_url"],
                "imgtaken_timestamp": row["collector_timestamp"],
                "uploaded_at": row["created_at"],
                "finder_id": row["finder_user_id"],
            }
            for row in rows
        ]
