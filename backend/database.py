import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional

_DEFAULT_DATABASE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "lost_and_found.db"
)
DATABASE_PATH = os.environ.get("DATABASE_PATH", _DEFAULT_DATABASE_PATH)
os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)


def _bool_to_int(value: Optional[bool]) -> Optional[int]:
    if value is None:
        return None
    return 1 if value else 0


@contextmanager
def get_db_connection():
    """Context manager that returns a SQLite connection with sensible defaults."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 15000;")
        yield conn
    finally:
        conn.close()


def init_database():
    """Initialise the SQLite database using the new schema."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS User (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                password TEXT,
                phone_number TEXT,
                email TEXT UNIQUE,
                student_id TEXT,
                rfid_tag TEXT UNIQUE,
                items_found INTEGER DEFAULT 0,
                items_find INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Item (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                image_url TEXT,
                finder_user_id INTEGER,
                finder_img_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (finder_user_id) REFERENCES User(user_id)
                    ON UPDATE CASCADE
                    ON DELETE SET NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Box (
                box_id INTEGER PRIMARY KEY AUTOINCREMENT,
                status INTEGER DEFAULT 1,
                location TEXT,
                load INTEGER DEFAULT 0,
                door_status INTEGER DEFAULT 0,
                last_accessed DATETIME
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "Case" (
                found_id INTEGER PRIMARY KEY AUTOINCREMENT,
                box_id INTEGER,
                reciver_image_url TEXT,
                reciver_id INTEGER,
                item_id INTEGER,
                status TEXT,
                case_close_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (box_id) REFERENCES Box(box_id)
                    ON UPDATE CASCADE
                    ON DELETE SET NULL,
                FOREIGN KEY (reciver_id) REFERENCES User(user_id)
                    ON UPDATE CASCADE
                    ON DELETE SET NULL,
                FOREIGN KEY (item_id) REFERENCES Item(item_id)
                    ON UPDATE CASCADE
                    ON DELETE SET NULL
            )
            """
        )

        # Helpful indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_description ON Item(description)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_case_status ON \"Case\"(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_case_box ON \"Case\"(box_id)")

        conn.commit()


# ---------------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------------

def create_user(
    name: str,
    password: Optional[str] = None,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
    student_id: Optional[str] = None,
    rfid_tag: Optional[str] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO User (name, password, phone_number, email, student_id, rfid_tag)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, password, phone_number, email, student_id, rfid_tag),
        )
        conn.commit()
        return cursor.lastrowid


def get_user_by_id(user_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE user_id = ?", (user_id,))
        return cursor.fetchone()


def get_user_by_email(email: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE email = ?", (email,))
        return cursor.fetchone()


def get_user_by_rfid(rfid_tag: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE rfid_tag = ?", (rfid_tag,))
        return cursor.fetchone()


def get_user_by_student_id(student_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE student_id = ?", (student_id,))
        return cursor.fetchone()


def list_users():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User ORDER BY created_at DESC")
        return cursor.fetchall()


def increment_user_items_found(user_id: int, amount: int = 1) -> None:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE User SET items_found = items_found + ? WHERE user_id = ?",
            (amount, user_id),
        )
        conn.commit()


def increment_user_items_claimed(user_id: int, amount: int = 1) -> None:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE User SET items_find = items_find + ? WHERE user_id = ?",
            (amount, user_id),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Item helpers
# ---------------------------------------------------------------------------

def create_item(
    description: Optional[str],
    image_url: Optional[str],
    finder_user_id: Optional[int] = None,
    finder_img_url: Optional[str] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Item (description, image_url, finder_user_id, finder_img_url)
            VALUES (?, ?, ?, ?)
            """,
            (description, image_url, finder_user_id, finder_img_url),
        )
        conn.commit()
        return cursor.lastrowid


def update_item_finder_image(item_id: int, finder_img_url: str) -> None:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Item SET finder_img_url = ? WHERE item_id = ?",
            (finder_img_url, item_id),
        )
        conn.commit()


def get_item_by_id(item_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Item WHERE item_id = ?", (item_id,))
        return cursor.fetchone()


def get_item_by_image_url(image_url: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Item WHERE image_url = ?", (image_url,))
        return cursor.fetchone()


def list_items():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT i.*, u.name AS finder_name
            FROM Item i
            LEFT JOIN User u ON i.finder_user_id = u.user_id
            ORDER BY i.created_at DESC
            """
        )
        return cursor.fetchall()


def delete_item(item_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Item WHERE item_id = ?", (item_id,))
        conn.commit()
        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Box helpers
# ---------------------------------------------------------------------------

def create_box(
    location: str,
    status: bool = True,
    load: int = 0,
    door_status: bool = False,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Box (status, location, load, door_status, last_accessed)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                _bool_to_int(status),
                location,
                load,
                _bool_to_int(door_status),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def update_box(
    box_id: int,
    *,
    status: Optional[bool] = None,
    location: Optional[str] = None,
    load: Optional[int] = None,
    door_status: Optional[bool] = None,
) -> int:
    fields = []
    values: list = []

    if status is not None:
        fields.append("status = ?")
        values.append(_bool_to_int(status))
    if location is not None:
        fields.append("location = ?")
        values.append(location)
    if load is not None:
        fields.append("load = ?")
        values.append(load)
    if door_status is not None:
        fields.append("door_status = ?")
        values.append(_bool_to_int(door_status))

    if not fields:
        return 0

    fields.append("last_accessed = ?")
    values.append(datetime.utcnow().isoformat())
    values.append(box_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE Box SET {', '.join(fields)} WHERE box_id = ?",
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount


def get_box(box_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Box WHERE box_id = ?", (box_id,))
        return cursor.fetchone()


def list_boxes():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Box ORDER BY box_id")
        return cursor.fetchall()


# ---------------------------------------------------------------------------
# Case helpers
# ---------------------------------------------------------------------------

def create_case(
    box_id: int,
    *,
    reciver_image_url: Optional[str] = None,
    reciver_id: Optional[int] = None,
    item_id: Optional[int] = None,
    status: str = "available",
    case_close_at: Optional[str] = None,
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO "Case" (box_id, reciver_image_url, reciver_id, item_id, status, case_close_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (box_id, reciver_image_url, reciver_id, item_id, status, case_close_at),
        )
        conn.commit()
        return cursor.lastrowid


def update_case(
    found_id: int,
    *,
    box_id: Optional[int] = None,
    reciver_image_url: Optional[str] = None,
    reciver_id: Optional[int] = None,
    item_id: Optional[int] = None,
    status: Optional[str] = None,
    case_close_at: Optional[str] = None,
) -> int:
    fields: list[str] = []
    values: list = []

    if box_id is not None:
        fields.append("box_id = ?")
        values.append(box_id)
    if reciver_image_url is not None:
        fields.append("reciver_image_url = ?")
        values.append(reciver_image_url)
    if reciver_id is not None:
        fields.append("reciver_id = ?")
        values.append(reciver_id)
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
            f"UPDATE \"Case\" SET {', '.join(fields)} WHERE found_id = ?",
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount


def get_case(found_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM \"Case\" WHERE found_id = ?", (found_id,))
        return cursor.fetchone()


def list_cases():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.*, i.description, i.image_url, b.location
            FROM "Case" c
            LEFT JOIN Item i ON c.item_id = i.item_id
            LEFT JOIN Box b ON c.box_id = b.box_id
            ORDER BY c.created_at DESC
            """
        )
        return cursor.fetchall()


def delete_case(found_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM \"Case\" WHERE found_id = ?", (found_id,))
        conn.commit()
        return cursor.rowcount > 0


def search_cases(query: str):
    pattern = f"%{query.strip()}%"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.found_id, c.status, c.case_close_at, c.created_at,
                   c.reciver_id, c.reciver_image_url,
                   i.item_id, i.description, i.image_url, i.finder_user_id, i.finder_img_url,
                   b.box_id, b.location, b.status AS box_status, b.load, b.door_status, b.last_accessed,
                   u.name AS finder_name
            FROM "Case" c
            LEFT JOIN Item i ON c.item_id = i.item_id
            LEFT JOIN Box b ON c.box_id = b.box_id
            LEFT JOIN User u ON i.finder_user_id = u.user_id
            WHERE i.description LIKE ? OR i.image_url LIKE ?
            ORDER BY c.created_at DESC
            """,
            (pattern, pattern),
        )
        return cursor.fetchall()


def claim_case(found_id: int, receiver_id: int, hold_minutes: int = 60):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM \"Case\" WHERE found_id = ?", (found_id,))
        case_row = cursor.fetchone()
        if not case_row:
            return False, "Case not found"

        status = case_row["status"] or "available"
        case_close_at = case_row["case_close_at"]

        if status == "claimed" and case_close_at:
            expires = datetime.fromisoformat(case_close_at)
            if datetime.utcnow() < expires:
                return False, "Case is currently claimed"

        claim_until = datetime.utcnow() + timedelta(minutes=hold_minutes)
        cursor.execute(
            """
            UPDATE "Case"
            SET status = ?, reciver_id = ?, case_close_at = ?
            WHERE found_id = ?
            """,
            ("claimed", receiver_id, claim_until.isoformat(), found_id),
        )
        increment_user_items_claimed(receiver_id, 1)
        conn.commit()
        return True, "Case claimed successfully"


def release_expired_cases() -> int:
    now_iso = datetime.utcnow().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE "Case"
            SET status = 'available', reciver_id = NULL, case_close_at = NULL
            WHERE status = 'claimed' AND case_close_at IS NOT NULL AND case_close_at < ?
            """,
            (now_iso,),
        )
        conn.commit()
        return cursor.rowcount


# Ensure the database exists when the module is imported in a cold environment
if not os.path.exists(DATABASE_PATH):
    init_database()
