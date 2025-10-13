import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lost_and_found.db")

USER_TABLE = "User"
ITEM_TABLE = "Item"
BOX_TABLE = "Box"
CASE_TABLE = "Case"


@contextmanager
def get_db_connection():
    """Yield a SQLite connection configured for concurrent access."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=15000;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
    finally:
        conn.close()


def init_database() -> None:
    """Initialise the database schema."""
    schema_sql = f"""
    CREATE TABLE IF NOT EXISTS {USER_TABLE} (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        rfid_tag TEXT UNIQUE,
        student_id TEXT UNIQUE,
        id_number TEXT,
        user_type TEXT NOT NULL DEFAULT 'both',
        items_find INTEGER NOT NULL DEFAULT 0,
        items_collect INTEGER NOT NULL DEFAULT 0,
        reputation_score REAL NOT NULL DEFAULT 0.0,
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_active DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS {ITEM_TABLE} (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL UNIQUE,
        description TEXT,
        image_embedding TEXT NOT NULL,
        description_embedding TEXT,
        status TEXT NOT NULL DEFAULT 'available',
        claimed_at DATETIME,
        claimed_by_user_id INTEGER,
        finder_user_id INTEGER,
        uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME,
        collected_at DATETIME,
        FOREIGN KEY (claimed_by_user_id) REFERENCES {USER_TABLE} (user_id) ON DELETE SET NULL,
        FOREIGN KEY (finder_user_id) REFERENCES {USER_TABLE} (user_id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS {BOX_TABLE} (
        box_id INTEGER PRIMARY KEY AUTOINCREMENT,
        status TEXT NOT NULL DEFAULT 'available',
        location TEXT,
        door_status TEXT NOT NULL DEFAULT 'closed',
        capacity INTEGER NOT NULL DEFAULT 1,
        current_load INTEGER NOT NULL DEFAULT 0,
        last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS {CASE_TABLE} (
        case_id INTEGER PRIMARY KEY AUTOINCREMENT,
        box_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        reciver_id INTEGER,
        receiver_image_url TEXT,
        status TEXT NOT NULL DEFAULT 'available',
        case_close_at DATETIME,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (box_id) REFERENCES {BOX_TABLE} (box_id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES {ITEM_TABLE} (item_id) ON DELETE CASCADE,
        FOREIGN KEY (reciver_id) REFERENCES {USER_TABLE} (user_id) ON DELETE SET NULL
    );

    CREATE INDEX IF NOT EXISTS idx_item_status ON {ITEM_TABLE} (status);
    CREATE INDEX IF NOT EXISTS idx_item_finder ON {ITEM_TABLE} (finder_user_id);
    CREATE INDEX IF NOT EXISTS idx_case_box ON {CASE_TABLE} (box_id);
    CREATE INDEX IF NOT EXISTS idx_case_item ON {CASE_TABLE} (item_id);
    """

    with sqlite3.connect(DATABASE_PATH, timeout=15.0) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=15000;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.executescript(schema_sql)
        conn.commit()

    migrate_legacy_schema()


def _table_exists(cursor: sqlite3.Cursor, name: str) -> bool:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND lower(name) = lower(?)", (name,))
    return cursor.fetchone() is not None


def _table_is_empty(cursor: sqlite3.Cursor, table: str) -> bool:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    return cursor.fetchone()[0] == 0


def _safe_datetime(value: Any) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value).isoformat()
        except (ValueError, OSError):
            return None
    return str(value)

def migrate_legacy_schema() -> None:
    """Copy existing records from legacy tables into the new schema."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if _table_exists(cursor, "USERS") and _table_is_empty(cursor, USER_TABLE):
            cursor.execute("SELECT * FROM USERS")
            for row in cursor.fetchall():
                record = dict(row)
                cursor.execute(
                    f"""
                    INSERT OR IGNORE INTO {USER_TABLE}
                    (user_id, name, email, phone, rfid_tag, student_id, id_number, user_type,
                     items_find, items_collect, reputation_score, verification_status, created_at, last_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.get("user_id"),
                        record.get("name"),
                        record.get("email"),
                        record.get("phone"),
                        record.get("rfid_tag"),
                        record.get("student_id"),
                        record.get("id_number"),
                        record.get("user_type", "both"),
                        record.get("items_found", record.get("items_find", 0)),
                        record.get("items_claimed", record.get("items_collect", 0)),
                        record.get("reputation_score", 0.0),
                        record.get("verification_status", "unverified"),
                        record.get("created_at", datetime.now().isoformat()),
                        record.get("last_active", datetime.now().isoformat()),
                    ),
                )
            try:
                cursor.execute("ALTER TABLE USERS RENAME TO USERS_LEGACY")
            except sqlite3.OperationalError:
                pass

        if _table_exists(cursor, "FINDERS"):
            cursor.execute("SELECT * FROM FINDERS")
            for row in cursor.fetchall():
                record = dict(row)
                email = record.get("email")
                cursor.execute(f"SELECT user_id, user_type FROM {USER_TABLE} WHERE email = ?", (email,))
                existing = cursor.fetchone()
                if existing:
                    new_type = existing[1]
                    if new_type == "collector":
                        new_type = "both"
                    cursor.execute(
                        f"UPDATE {USER_TABLE} SET user_type = ?, items_find = COALESCE(items_find, 0) + ?, last_active = ? WHERE user_id = ?",
                        (new_type, record.get("items_found", 0), datetime.now().isoformat(), existing[0]),
                    )
                else:
                    cursor.execute(
                        f"""
                        INSERT OR IGNORE INTO {USER_TABLE}
                        (name, email, phone, rfid_tag, user_type, items_find, created_at, last_active)
                        VALUES (?, ?, ?, ?, 'finder', ?, ?, ?)
                        """,
                        (
                            record.get("name"),
                            email,
                            record.get("phone"),
                            record.get("rfid_tag"),
                            record.get("items_found", 0),
                            record.get("created_at", datetime.now().isoformat()),
                            record.get("last_active", datetime.now().isoformat()),
                        ),
                    )
            try:
                cursor.execute("ALTER TABLE FINDERS RENAME TO FINDERS_LEGACY")
            except sqlite3.OperationalError:
                pass

        if _table_exists(cursor, "COLLECTORS"):
            cursor.execute("SELECT * FROM COLLECTORS")
            for row in cursor.fetchall():
                record = dict(row)
                email = record.get("email")
                cursor.execute(f"SELECT user_id, user_type FROM {USER_TABLE} WHERE email = ?", (email,))
                existing = cursor.fetchone()
                if existing:
                    new_type = existing[1]
                    if new_type == "finder":
                        new_type = "both"
                    cursor.execute(
                        f"UPDATE {USER_TABLE} SET user_type = ?, items_collect = COALESCE(items_collect, 0) + ?, verification_status = COALESCE(?, verification_status), last_active = ? WHERE user_id = ?",
                        (new_type, record.get("items_claimed", 0), record.get("verification_status"), datetime.now().isoformat(), existing[0]),
                    )
                else:
                    cursor.execute(
                        f"""
                        INSERT OR IGNORE INTO {USER_TABLE}
                        (name, email, phone, student_id, id_number, user_type, items_collect, verification_status, created_at, last_active)
                        VALUES (?, ?, ?, ?, ?, 'collector', ?, COALESCE(?, 'unverified'), ?, ?)
                        """,
                        (
                            record.get("name"),
                            email,
                            record.get("phone"),
                            record.get("student_id"),
                            record.get("id_number"),
                            record.get("items_claimed", 0),
                            record.get("verification_status"),
                            record.get("created_at", datetime.now().isoformat()),
                            record.get("last_active", datetime.now().isoformat()),
                        ),
                    )
            try:
                cursor.execute("ALTER TABLE COLLECTORS RENAME TO COLLECTORS_LEGACY")
            except sqlite3.OperationalError:
                pass

        if _table_exists(cursor, "BOXES") and _table_is_empty(cursor, BOX_TABLE):
            cursor.execute("SELECT * FROM BOXES")
            for row in cursor.fetchall():
                record = dict(row)
                legacy_id = record.get("box_id") or record.get("id")
                status_value = record.get("status")
                if isinstance(status_value, (int, float)):
                    status = "available" if status_value else "unavailable"
                else:
                    status = status_value or "available"
                door_value = record.get("door_status")
                if str(door_value).lower() in {"1", "true", "open"}:
                    door_status = "open"
                else:
                    door_status = "closed"
                cursor.execute(
                    f"""
                    INSERT OR IGNORE INTO {BOX_TABLE}
                    (box_id, status, location, door_status, capacity, current_load, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        legacy_id,
                        status,
                        record.get("location"),
                        door_status,
                        record.get("capacity", record.get("max_capacity", 1)),
                        record.get("current_load", record.get("load", 0)),
                        record.get("last_updated", record.get("last_accessed", datetime.now().isoformat())),
                    ),
                )
            try:
                cursor.execute("ALTER TABLE BOXES RENAME TO BOXES_LEGACY")
            except sqlite3.OperationalError:
                pass

        if _table_exists(cursor, "FOUND_ITEMS") and _table_is_empty(cursor, ITEM_TABLE):
            cursor.execute("SELECT * FROM FOUND_ITEMS")
            for row in cursor.fetchall():
                record = dict(row)
                cursor.execute(
                    f"""
                    INSERT OR IGNORE INTO {ITEM_TABLE}
                    (item_id, filename, description, image_embedding, description_embedding, status,
                     claimed_at, claimed_by_user_id, finder_user_id, uploaded_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.get("id"),
                        record.get("filename"),
                        record.get("description"),
                        record.get("image_embedding"),
                        record.get("description_embedding"),
                        record.get("status", "available"),
                        record.get("claimed_at"),
                        record.get("claimed_by"),
                        record.get("finder_id"),
                        record.get("uploaded_at"),
                        record.get("expires_at"),
                    ),
                )
            try:
                cursor.execute("ALTER TABLE FOUND_ITEMS RENAME TO FOUND_ITEMS_LEGACY")
            except sqlite3.OperationalError:
                pass

        if _table_exists(cursor, "CASES") and _table_is_empty(cursor, CASE_TABLE):
            cursor.execute("SELECT * FROM CASES")
            for row in cursor.fetchall():
                record = dict(row)
                cursor.execute(
                    f"""
                    INSERT OR IGNORE INTO {CASE_TABLE}
                    (case_id, box_id, item_id, reciver_id, receiver_image_url, status, case_close_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.get("found_id"),
                        record.get("box_id"),
                        record.get("item_id"),
                        record.get("receiver_id"),
                        record.get("receiver_image_url"),
                        record.get("status", "available"),
                        record.get("case_close_at"),
                        record.get("created_at", datetime.now().isoformat()),
                    ),
                )
            try:
                cursor.execute("ALTER TABLE CASES RENAME TO CASES_LEGACY")
            except sqlite3.OperationalError:
                pass

        if _table_exists(cursor, "COLLECTED_ITEMS"):
            cursor.execute(f"SELECT filename, item_id FROM {ITEM_TABLE}")
            filename_to_item = {row[0]: row[1] for row in cursor.fetchall()}
            cursor.execute("SELECT * FROM COLLECTED_ITEMS")
            for row in cursor.fetchall():
                record = dict(row)
                item_id = filename_to_item.get(record.get("filename"))
                if not item_id:
                    continue
                collected_at = _safe_datetime(record.get("imgtaken_timestamp"))
                if collected_at:
                    cursor.execute(
                        f"UPDATE {ITEM_TABLE} SET collected_at = ?, status = 'collected' WHERE item_id = ?",
                        (collected_at, item_id),
                    )
                cursor.execute(
                    f"""
                    INSERT INTO {CASE_TABLE}
                    (box_id, item_id, reciver_id, status, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        record.get("box_id"),
                        item_id,
                        record.get("finder_id"),
                        "collected",
                        record.get("uploaded_at", datetime.now().isoformat()),
                    ),
                )
            try:
                cursor.execute("ALTER TABLE COLLECTED_ITEMS RENAME TO COLLECTED_ITEMS_LEGACY")
            except sqlite3.OperationalError:
                pass

        conn.commit()

# ---------------------------------------------------------------------------
# Helper conversions
# ---------------------------------------------------------------------------

def _row_to_user_dict(row: Optional[sqlite3.Row], role: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    data = dict(row)
    data.setdefault("items_find", data.get("items_find", 0))
    data.setdefault("items_collect", data.get("items_collect", 0))
    data["items_found"] = data.get("items_find", 0)
    data["items_claimed"] = data.get("items_collect", 0)
    data["finder_id"] = data.get("user_id")
    data["collector_id"] = data.get("user_id")
    data["reputation_score"] = data.get("reputation_score", 0.0)
    data["verification_status"] = data.get("verification_status", "unverified")
    if role:
        data["user_type"] = role
    return data


def _row_to_item_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    data = dict(row)
    data["id"] = data.get("item_id")
    data.setdefault("finder_id", data.get("finder_user_id"))
    data.setdefault("claimed_by", data.get("claimed_by_user_id"))
    return data


def _row_to_case_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    data = dict(row)
    data["case_id"] = data.get("case_id")
    data["found_id"] = data.get("case_id")
    data["receiver_id"] = data.get("reciver_id")
    return data


def _row_to_box_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return dict(row)


def _rows_to_dicts(rows: Iterable[sqlite3.Row], normaliser) -> List[Dict[str, Any]]:
    return [normaliser(row) for row in rows]

# ---------------------------------------------------------------------------
# Item helpers
# ---------------------------------------------------------------------------

def add_found_item(
    filename: str,
    image_embedding: Iterable[float],
    description: str = "",
    description_embedding: Optional[Iterable[float]] = None,
    finder_user_id: Optional[int] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        img_emb_json = json.dumps(list(image_embedding))
        desc_emb_json = json.dumps(list(description_embedding)) if description_embedding is not None else None
        cursor.execute(
            f"""
            INSERT INTO {ITEM_TABLE}
            (filename, description, image_embedding, description_embedding, finder_user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (filename, description, img_emb_json, desc_emb_json, finder_user_id),
        )
        conn.commit()
        return cursor.lastrowid


def get_available_items() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        cursor.execute(
            f"""
            SELECT * FROM {ITEM_TABLE}
            WHERE status = 'available'
               OR (status = 'claimed' AND expires_at IS NOT NULL AND datetime(expires_at) < datetime(?))
            """,
            (current_time,),
        )
        return _rows_to_dicts(cursor.fetchall(), _row_to_item_dict)


def get_all_items() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {ITEM_TABLE}")
        return _rows_to_dicts(cursor.fetchall(), _row_to_item_dict)


def claim_item(item_id: int, claimed_by_collector_id: int) -> Tuple[bool, str]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT status, expires_at FROM {ITEM_TABLE} WHERE item_id = ?",
            (item_id,),
        )
        row = cursor.fetchone()
        if not row:
            return False, "Item not found"
        status, expires_at = row["status"], row["expires_at"]
        if status == "claimed" and expires_at:
            expires_datetime = datetime.fromisoformat(expires_at)
            if datetime.now() < expires_datetime:
                return False, "Item is currently claimed"
        claimed_at = datetime.now()
        expires_at = claimed_at + timedelta(minutes=1)
        cursor.execute(
            f"""
            UPDATE {ITEM_TABLE}
            SET status = 'claimed', claimed_at = ?, claimed_by_user_id = ?, expires_at = ?
            WHERE item_id = ?
            """,
            (claimed_at.isoformat(), claimed_by_collector_id, expires_at.isoformat(), item_id),
        )
        conn.commit()

    try:
        update_collector_stats(claimed_by_collector_id, items_claimed_increment=1)
    except Exception as exc:  # pragma: no cover - best effort
        logging.warning("Unable to update collector stats: %s", exc)
    return True, "Item claimed successfully"


def release_expired_claims() -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        cursor.execute(
            f"""
            UPDATE {ITEM_TABLE}
            SET status = 'available', claimed_at = NULL, claimed_by_user_id = NULL, expires_at = NULL
            WHERE status = 'claimed' AND expires_at IS NOT NULL AND datetime(expires_at) < datetime(?)
            """,
            (current_time,),
        )
        conn.commit()
        return cursor.rowcount


def delete_item(filename: str) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {ITEM_TABLE} WHERE filename = ?", (filename,))
        conn.commit()
        return cursor.rowcount > 0


def get_item_by_filename(filename: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {ITEM_TABLE} WHERE filename = ?", (filename,))
        return _row_to_item_dict(cursor.fetchone())


def search_items(query_embedding: Iterable[float], threshold: float = 0.4) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        cursor.execute(
            f"""
            SELECT * FROM {ITEM_TABLE}
            WHERE status = 'available'
               OR (status = 'claimed' AND expires_at IS NOT NULL AND datetime(expires_at) < datetime(?))
            """,
            (current_time,),
        )
        items = cursor.fetchall()

    results: List[Dict[str, Any]] = []
    query_emb = np.array(list(query_embedding), dtype=np.float32)

    for item in items:
        data = dict(item)
        img_emb = np.array(json.loads(data["image_embedding"]), dtype=np.float32)
        img_score = float(np.dot(query_emb, img_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(img_emb)))
        desc_score = 0.0
        if data.get("description_embedding"):
            desc_emb = np.array(json.loads(data["description_embedding"]), dtype=np.float32)
            desc_score = float(np.dot(query_emb, desc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(desc_emb)))
        final_score = 0.6 * desc_score + 0.4 * img_score
        if final_score > threshold:
            status = data["status"]
            if status == "claimed" and data.get("expires_at"):
                expires_datetime = datetime.fromisoformat(data["expires_at"])
                if datetime.now() > expires_datetime:
                    release_expired_claims()
                    status = "available"
            results.append(
                {
                    "id": data["item_id"],
                    "item_id": data["item_id"],
                    "filename": data["filename"],
                    "description": data.get("description"),
                    "score": final_score,
                    "status": status,
                    "claimed_by": data.get("claimed_by_user_id"),
                    "expires_at": data.get("expires_at"),
                    "uploaded_at": data.get("uploaded_at"),
                }
            )
    return results


def collect_found_item(
    filename: str,
    imgtaken_timestamp: Optional[float],
    box_id: int,
    finder_id: Optional[int] = None,
) -> int:
    item = get_item_by_filename(filename)
    if not item:
        raise ValueError(f"Item with filename {filename} does not exist")

    collected_at = _safe_datetime(imgtaken_timestamp)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if collected_at:
            cursor.execute(
                f"UPDATE {ITEM_TABLE} SET collected_at = ?, status = 'collected' WHERE item_id = ?",
                (collected_at, item["item_id"]),
            )
        cursor.execute(
            f"""
            INSERT INTO {CASE_TABLE} (box_id, item_id, reciver_id, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                box_id,
                item["item_id"],
                finder_id,
                "collected",
                datetime.now().isoformat(),
            ),
        )
        case_id = cursor.lastrowid
        conn.commit()

    if finder_id:
        update_finder_stats(finder_id, items_found_increment=1)
    return case_id


def get_collected_items() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT c.case_id, i.filename, c.box_id, c.reciver_id AS finder_id, i.collected_at AS imgtaken_timestamp,
                   c.created_at AS uploaded_at
            FROM {CASE_TABLE} c
            JOIN {ITEM_TABLE} i ON i.item_id = c.item_id
            WHERE c.status = 'collected'
            ORDER BY c.created_at DESC
            """,
        )
        rows = cursor.fetchall()

    results: List[Dict[str, Any]] = []
    for row in rows:
        data = dict(row)
        data["id"] = data["case_id"]
        results.append(data)
    return results


def clear_all_items() -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {ITEM_TABLE}")
        conn.commit()
        return cursor.rowcount

# ---------------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------------

def add_user(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    rfid_tag: Optional[str] = None,
    student_id: Optional[str] = None,
    user_type: str = "both",
    id_number: Optional[str] = None,
) -> int:
    now = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {USER_TABLE}
            (name, email, phone, rfid_tag, student_id, id_number, user_type, created_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, email, phone, rfid_tag, student_id, id_number, user_type, now, now),
        )
        conn.commit()
        return cursor.lastrowid


def add_finder(name: str, email: Optional[str] = None, phone: Optional[str] = None, rfid_tag: Optional[str] = None) -> int:
    return add_user(name, email, phone, rfid_tag, None, "finder")


def add_collector(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    student_id: Optional[str] = None,
    id_number: Optional[str] = None,
) -> int:
    return add_user(name, email, phone, None, student_id, "collector", id_number=id_number)


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {USER_TABLE} WHERE user_id = ?", (user_id,))
        return _row_to_user_dict(cursor.fetchone())


def get_finder_by_id(finder_id: int) -> Optional[Dict[str, Any]]:
    return get_user_by_id(finder_id)


def get_collector_by_id(collector_id: int) -> Optional[Dict[str, Any]]:
    return get_user_by_id(collector_id)


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {USER_TABLE} WHERE email = ?", (email,))
        return _row_to_user_dict(cursor.fetchone())


def get_finder_by_email(email: str) -> Optional[Dict[str, Any]]:
    return get_user_by_email(email)


def get_collector_by_email(email: str) -> Optional[Dict[str, Any]]:
    return get_user_by_email(email)


def get_user_by_rfid(rfid_tag: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {USER_TABLE} WHERE rfid_tag = ?", (rfid_tag,))
        return _row_to_user_dict(cursor.fetchone())


def get_finder_by_rfid(rfid_tag: str) -> Optional[Dict[str, Any]]:
    return get_user_by_rfid(rfid_tag)


def get_user_by_student_id(student_id: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {USER_TABLE} WHERE student_id = ?", (student_id,))
        return _row_to_user_dict(cursor.fetchone())


def get_collector_by_student_id(student_id: str) -> Optional[Dict[str, Any]]:
    return get_user_by_student_id(student_id)


def update_user_stats(
    user_id: int,
    items_found_increment: int = 0,
    items_claimed_increment: int = 0,
    reputation_increment: float = 0.0,
    verification_status: Optional[str] = None,
) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        fields = ["items_find = items_find + ?", "items_collect = items_collect + ?", "reputation_score = reputation_score + ?", "last_active = ?"]
        values: List[Any] = [items_found_increment, items_claimed_increment, reputation_increment, datetime.now().isoformat()]
        if verification_status is not None:
            fields.append("verification_status = ?")
            values.append(verification_status)
        values.append(user_id)
        cursor.execute(
            f"UPDATE {USER_TABLE} SET {', '.join(fields)} WHERE user_id = ?",
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_finder_stats(finder_id: int, items_found_increment: int = 0, reputation_increment: float = 0.0) -> bool:
    return update_user_stats(finder_id, items_found_increment=items_found_increment, reputation_increment=reputation_increment)


def update_collector_stats(
    collector_id: int,
    items_claimed_increment: int = 0,
    verification_status: Optional[str] = None,
) -> bool:
    return update_user_stats(collector_id, items_claimed_increment=items_claimed_increment, verification_status=verification_status)


def get_all_finders() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM {USER_TABLE} WHERE user_type IN ('finder', 'both') ORDER BY created_at DESC"
        )
        return _rows_to_dicts(cursor.fetchall(), lambda row: _row_to_user_dict(row, role="finder"))


def get_all_collectors() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM {USER_TABLE} WHERE user_type IN ('collector', 'both') ORDER BY created_at DESC"
        )
        return _rows_to_dicts(cursor.fetchall(), lambda row: _row_to_user_dict(row, role="collector"))

# ---------------------------------------------------------------------------
# Box helpers
# ---------------------------------------------------------------------------

def add_box(location: str, status: bool = True, door_status: bool = False, load: int = 0, capacity: int = 1) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {BOX_TABLE} (status, location, door_status, current_load, capacity, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "available" if status else "unavailable",
                location,
                "open" if door_status else "closed",
                load,
                capacity,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def delete_box(box_id: int) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {BOX_TABLE} WHERE box_id = ?", (box_id,))
        conn.commit()
        return cursor.rowcount


def update_box(
    box_id: int,
    status: Optional[bool] = None,
    door_status: Optional[bool] = None,
    location: Optional[str] = None,
    load: Optional[int] = None,
    capacity: Optional[int] = None,
) -> int:
    fields: List[str] = []
    values: List[Any] = []
    if status is not None:
        fields.append("status = ?")
        values.append("available" if status else "unavailable")
    if door_status is not None:
        fields.append("door_status = ?")
        values.append("open" if door_status else "closed")
    if location is not None:
        fields.append("location = ?")
        values.append(location)
    if load is not None:
        fields.append("current_load = ?")
        values.append(load)
    if capacity is not None:
        fields.append("capacity = ?")
        values.append(capacity)
    fields.append("last_updated = ?")
    values.append(datetime.now().isoformat())
    values.append(box_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {BOX_TABLE} SET {', '.join(fields)} WHERE box_id = ?",
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount


def get_box_status(box_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {BOX_TABLE} WHERE box_id = ?", (box_id,))
        return _row_to_box_dict(cursor.fetchone())


def update_box_status(
    box_id: int,
    status: Optional[str] = None,
    current_load: Optional[int] = None,
    door_status: Optional[str] = None,
    capacity: Optional[int] = None,
) -> int:
    fields: List[str] = []
    values: List[Any] = []
    if status is not None:
        fields.append("status = ?")
        values.append(status)
    if current_load is not None:
        fields.append("current_load = ?")
        values.append(current_load)
    if door_status is not None:
        fields.append("door_status = ?")
        values.append(door_status)
    if capacity is not None:
        fields.append("capacity = ?")
        values.append(capacity)
    if not fields:
        return 0
    fields.append("last_updated = ?")
    values.append(datetime.now().isoformat())
    values.append(box_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {BOX_TABLE} SET {', '.join(fields)} WHERE box_id = ?",
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount


def get_all_boxes() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {BOX_TABLE} ORDER BY box_id")
        return _rows_to_dicts(cursor.fetchall(), _row_to_box_dict)

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
            INSERT INTO {CASE_TABLE} (box_id, reciver_id, receiver_image_url, item_id, status, case_close_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                box_id,
                receiver_id,
                receiver_image_url,
                item_id,
                status,
                case_close_at,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def update_case(
    case_id: int,
    box_id: Optional[int] = None,
    receiver_id: Optional[int] = None,
    receiver_image_url: Optional[str] = None,
    item_id: Optional[int] = None,
    status: Optional[str] = None,
    case_close_at: Optional[str] = None,
) -> int:
    fields: List[str] = []
    values: List[Any] = []
    if box_id is not None:
        fields.append("box_id = ?")
        values.append(box_id)
    if receiver_id is not None:
        fields.append("reciver_id = ?")
        values.append(receiver_id)
    if receiver_image_url is not None:
        fields.append("receiver_image_url = ?")
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
    values.append(case_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {CASE_TABLE} SET {', '.join(fields)} WHERE case_id = ?",
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount


def delete_case(case_id: int) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {CASE_TABLE} WHERE case_id = ?", (case_id,))
        conn.commit()
        return cursor.rowcount


def get_case(case_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {CASE_TABLE} WHERE case_id = ?", (case_id,))
        return _row_to_case_dict(cursor.fetchone())


def get_all_case() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {CASE_TABLE} ORDER BY case_id")
        return _rows_to_dicts(cursor.fetchall(), _row_to_case_dict)
