import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Iterator, Optional

import numpy as np

# Use absolute path to ensure consistent database location
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lost_and_found.db')

logger = logging.getLogger(__name__)


def init_database() -> None:
    """Initialise the database using the unified schema."""
    with sqlite3.connect(DATABASE_PATH, timeout=15.0) as conn:
        cursor = conn.cursor()
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('PRAGMA busy_timeout=15000;')
        cursor.execute('PRAGMA foreign_keys=ON;')

        _create_users_table(cursor)
        _create_items_table(cursor)
        _create_boxes_table(cursor)
        _create_cases_table(cursor)

        conn.commit()


def _create_users_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS USERS (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            password TEXT,
            phone_number INTEGER,
            email TEXT UNIQUE,
            student_id INTEGER,
            rfid_tag TEXT UNIQUE,
            id_number TEXT,
            role TEXT DEFAULT 'finder',
            items_found INTEGER DEFAULT 0,
            items_find INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_active DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    cursor.execute("PRAGMA table_info(USERS)")
    columns = {col[1] for col in cursor.fetchall()}

    def _add_column(name: str, definition: str) -> None:
        if name not in columns:
            cursor.execute(f"ALTER TABLE USERS ADD COLUMN {name} {definition}")
            columns.add(name)

    _add_column('password', 'TEXT')
    _add_column('phone_number', 'INTEGER')
    _add_column('id_number', 'TEXT')
    _add_column("role", "TEXT DEFAULT 'finder'")
    _add_column('items_find', 'INTEGER DEFAULT 0')
    _add_column('last_active', 'DATETIME DEFAULT CURRENT_TIMESTAMP')

    # Attempt to migrate legacy column values when present
    cursor.execute("PRAGMA table_info(USERS)")
    detailed_columns = {col[1]: col for col in cursor.fetchall()}
    if 'phone' in detailed_columns and 'phone_number' in detailed_columns:
        cursor.execute('UPDATE USERS SET phone_number = phone WHERE phone IS NOT NULL AND phone_number IS NULL')
    if 'items_claimed' in detailed_columns and 'items_find' in detailed_columns:
        cursor.execute('UPDATE USERS SET items_find = items_claimed WHERE items_claimed IS NOT NULL AND (items_find IS NULL OR items_find = 0)')
    if 'user_type' in detailed_columns and 'role' in detailed_columns:
        cursor.execute("UPDATE USERS SET role = user_type WHERE user_type IS NOT NULL")


def _create_items_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS ITEMS (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            image_url TEXT NOT NULL UNIQUE,
            image_embedding TEXT,
            description_embedding TEXT,
            status TEXT DEFAULT 'available',
            finder_user_id INTEGER,
            finder_img_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            claimed_by INTEGER,
            claimed_at DATETIME,
            expires_at DATETIME,
            FOREIGN KEY (finder_user_id) REFERENCES USERS(user_id),
            FOREIGN KEY (claimed_by) REFERENCES USERS(user_id)
        )
        '''
    )

    cursor.execute("PRAGMA table_info(ITEMS)")
    columns = {col[1] for col in cursor.fetchall()}

    def _add_column(name: str, definition: str) -> None:
        if name not in columns:
            cursor.execute(f"ALTER TABLE ITEMS ADD COLUMN {name} {definition}")
            columns.add(name)

    _add_column('image_embedding', 'TEXT')
    _add_column('description_embedding', 'TEXT')
    _add_column("status", "TEXT DEFAULT 'available'")
    _add_column('finder_user_id', 'INTEGER')
    _add_column('finder_img_url', 'TEXT')
    _add_column('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
    _add_column('claimed_by', 'INTEGER')
    _add_column('claimed_at', 'DATETIME')
    _add_column('expires_at', 'DATETIME')


def _create_boxes_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS BOXES (
            box_id INTEGER PRIMARY KEY AUTOINCREMENT,
            status INTEGER DEFAULT 1,
            location TEXT NOT NULL,
            load INTEGER DEFAULT 0,
            door_status INTEGER DEFAULT 0,
            last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    cursor.execute("PRAGMA table_info(BOXES)")
    columns = {col[1] for col in cursor.fetchall()}

    def _add_column(name: str, definition: str) -> None:
        if name not in columns:
            cursor.execute(f"ALTER TABLE BOXES ADD COLUMN {name} {definition}")
            columns.add(name)

    _add_column('status', 'INTEGER DEFAULT 1')
    _add_column('location', 'TEXT')
    _add_column('load', 'INTEGER DEFAULT 0')
    _add_column('door_status', 'INTEGER DEFAULT 0')
    _add_column('last_accessed', 'DATETIME DEFAULT CURRENT_TIMESTAMP')


def _create_cases_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS CASES (
            found_id INTEGER PRIMARY KEY AUTOINCREMENT,
            box_id INTEGER,
            receiver_image_url TEXT,
            receiver_id INTEGER,
            item_id INTEGER,
            status TEXT DEFAULT 'available',
            case_close_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (box_id) REFERENCES BOXES(box_id),
            FOREIGN KEY (receiver_id) REFERENCES USERS(user_id),
            FOREIGN KEY (item_id) REFERENCES ITEMS(item_id)
        )
        '''
    )

    cursor.execute("PRAGMA table_info(CASES)")
    columns = {col[1] for col in cursor.fetchall()}

    def _add_column(name: str, definition: str) -> None:
        if name not in columns:
            cursor.execute(f"ALTER TABLE CASES ADD COLUMN {name} {definition}")
            columns.add(name)

    _add_column('receiver_image_url', 'TEXT')
    _add_column('receiver_id', 'INTEGER')
    _add_column('item_id', 'INTEGER')
    _add_column("status", "TEXT DEFAULT 'available'")
    _add_column('case_close_at', 'DATETIME')
    _add_column('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')


@contextmanager
def get_db_connection() -> Iterator[sqlite3.Connection]:
    """Context manager that configures a connection with sensible defaults."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=15.0)
    try:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA busy_timeout=15000;')
        conn.execute('PRAGMA foreign_keys=ON;')
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------------

def add_user(
    name: str,
    email: Optional[str] = None,
    password: Optional[str] = None,
    phone_number: Optional[str] = None,
    student_id: Optional[str] = None,
    rfid_tag: Optional[str] = None,
    id_number: Optional[str] = None,
    role: str = 'finder'
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO USERS (
                name, email, password, phone_number, student_id, rfid_tag,
                id_number, role, items_found, items_find, created_at, last_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
            ''',
            (
                name,
                email,
                password,
                phone_number,
                student_id,
                rfid_tag,
                id_number,
                role,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def add_finder(name: str, email: Optional[str] = None, phone: Optional[str] = None, rfid_tag: Optional[str] = None,
               password: Optional[str] = None) -> int:
    return add_user(name, email, password, phone, None, rfid_tag, None, role='finder')


def add_collector(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    student_id: Optional[str] = None,
    id_number: Optional[str] = None,
    password: Optional[str] = None
) -> int:
    return add_user(name, email, password, phone, student_id, None, id_number, role='collector')


def _fetch_one(query: str, params: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        return cursor.fetchone()


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    return _fetch_one('SELECT * FROM USERS WHERE user_id = ?', (user_id,))


def get_finder_by_id(finder_id: int) -> Optional[sqlite3.Row]:
    return _fetch_one("SELECT * FROM USERS WHERE user_id = ? AND role IN ('finder', 'both')", (finder_id,))


def get_collector_by_id(collector_id: int) -> Optional[sqlite3.Row]:
    return _fetch_one("SELECT * FROM USERS WHERE user_id = ? AND role IN ('collector', 'both')", (collector_id,))


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    return _fetch_one('SELECT * FROM USERS WHERE email = ?', (email,))


def get_finder_by_email(email: str) -> Optional[sqlite3.Row]:
    return _fetch_one("SELECT * FROM USERS WHERE email = ? AND role IN ('finder', 'both')", (email,))


def get_collector_by_email(email: str) -> Optional[sqlite3.Row]:
    return _fetch_one("SELECT * FROM USERS WHERE email = ? AND role IN ('collector', 'both')", (email,))


def get_user_by_rfid(rfid_tag: str) -> Optional[sqlite3.Row]:
    return _fetch_one('SELECT * FROM USERS WHERE rfid_tag = ?', (rfid_tag,))


def get_finder_by_rfid(rfid_tag: str) -> Optional[sqlite3.Row]:
    return _fetch_one("SELECT * FROM USERS WHERE rfid_tag = ? AND role IN ('finder', 'both')", (rfid_tag,))


def get_user_by_student_id(student_id: str) -> Optional[sqlite3.Row]:
    return _fetch_one('SELECT * FROM USERS WHERE student_id = ?', (student_id,))


def get_collector_by_student_id(student_id: str) -> Optional[sqlite3.Row]:
    return _fetch_one(
        "SELECT * FROM USERS WHERE student_id = ? AND role IN ('collector', 'both')",
        (student_id,),
    )


def get_all_users() -> Iterable[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM USERS ORDER BY created_at DESC')
        return cursor.fetchall()


def get_all_finders() -> Iterable[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM USERS WHERE role IN ('finder', 'both') ORDER BY created_at DESC")
        return cursor.fetchall()


def get_all_collectors() -> Iterable[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM USERS WHERE role IN ('collector', 'both') ORDER BY created_at DESC")
        return cursor.fetchall()


def update_user_stats(user_id: int, items_found_increment: int = 0, items_find_increment: int = 0) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            UPDATE USERS
            SET items_found = items_found + ?,
                items_find = items_find + ?,
                last_active = ?
            WHERE user_id = ?
            ''',
            (items_found_increment, items_find_increment, datetime.now().isoformat(), user_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_finder_stats(finder_id: int, items_found_increment: int = 0) -> bool:
    return update_user_stats(finder_id, items_found_increment=items_found_increment)


def update_collector_stats(collector_id: int, items_find_increment: int = 0) -> bool:
    return update_user_stats(collector_id, items_find_increment=items_find_increment)


def update_user_last_active(user_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE USERS SET last_active = ? WHERE user_id = ?',
            (datetime.now().isoformat(), user_id),
        )
        conn.commit()
        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Item helpers
# ---------------------------------------------------------------------------

def _serialise_item(row: sqlite3.Row) -> Dict[str, Any]:
    item = dict(row)
    # Provide backwards compatible key expected by some routes/clients
    item.setdefault('filename', item.get('image_url'))
    return item


def add_found_item(
    image_url: str,
    image_embedding: Optional[Iterable[float]] = None,
    description: str = '',
    description_embedding: Optional[Iterable[float]] = None,
    status: str = 'available',
    finder_user_id: Optional[int] = None,
    finder_img_url: Optional[str] = None,
    created_at: Optional[str] = None
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO ITEMS (
                description, image_url, image_embedding, description_embedding,
                status, finder_user_id, finder_img_url, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                description,
                image_url,
                json.dumps(list(image_embedding)) if image_embedding is not None else None,
                json.dumps(list(description_embedding)) if description_embedding is not None else None,
                status,
                finder_user_id,
                finder_img_url,
                created_at or datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_available_items() -> Iterable[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        cursor.execute(
            '''
            SELECT * FROM ITEMS
            WHERE status = 'available'
               OR (status = 'claimed' AND expires_at IS NOT NULL AND datetime(expires_at) < datetime(?))
            ''',
            (current_time,),
        )
        return [
            _serialise_item(row)
            for row in cursor.fetchall()
        ]


def get_all_items() -> Iterable[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ITEMS ORDER BY created_at DESC')
        return [_serialise_item(row) for row in cursor.fetchall()]


def claim_item(item_id: int, claimed_by_user_id: int) -> (bool, str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status, expires_at FROM ITEMS WHERE item_id = ?', (item_id,))
        row = cursor.fetchone()
        if not row:
            return False, 'Item not found'

        status = row['status']
        expires_at = row['expires_at']

        if status == 'claimed' and expires_at:
            expires_datetime = datetime.fromisoformat(expires_at)
            if datetime.now() < expires_datetime:
                return False, 'Item is currently claimed'

        claimed_at = datetime.now()
        expires = claimed_at + timedelta(hours=1)
        cursor.execute(
            '''
            UPDATE ITEMS
            SET status = 'claimed', claimed_at = ?, claimed_by = ?, expires_at = ?
            WHERE item_id = ?
            ''',
            (claimed_at.isoformat(), claimed_by_user_id, expires.isoformat(), item_id),
        )
        conn.commit()

    try:
        update_collector_stats(claimed_by_user_id, items_find_increment=1)
    except Exception as exc:  # pragma: no cover - best effort logging
        logger.warning("Unable to update collector stats: %s", exc)

    return True, 'Item claimed successfully'


def release_expired_claims() -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        cursor.execute(
            '''
            UPDATE ITEMS
            SET status = 'available', claimed_at = NULL, claimed_by = NULL, expires_at = NULL
            WHERE status = 'claimed' AND expires_at IS NOT NULL AND datetime(expires_at) < datetime(?)
            ''',
            (current_time,),
        )
        conn.commit()
        return cursor.rowcount


def delete_item(image_url: str) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ITEMS WHERE image_url = ?', (image_url,))
        conn.commit()
        return cursor.rowcount > 0


def get_item_by_filename(image_url: str) -> Optional[Dict[str, Any]]:
    row = _fetch_one('SELECT * FROM ITEMS WHERE image_url = ?', (image_url,))
    return _serialise_item(row) if row else None


def search_items(query_embedding: Iterable[float], threshold: float = 0.4) -> Iterable[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        cursor.execute(
            '''
            SELECT * FROM ITEMS
            WHERE status = 'available'
               OR (status = 'claimed' AND expires_at IS NOT NULL AND datetime(expires_at) < datetime(?))
            ''',
            (current_time,),
        )
        items = cursor.fetchall()

    query_emb = np.array(list(query_embedding), dtype=np.float32)
    results = []
    for item in items:
        image_embedding = item['image_embedding']
        if not image_embedding:
            continue
        img_emb = np.array(json.loads(image_embedding), dtype=np.float32)
        img_score = float(np.dot(query_emb, img_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(img_emb)))

        desc_score = 0.0
        if item['description_embedding']:
            desc_emb = np.array(json.loads(item['description_embedding']), dtype=np.float32)
            desc_score = float(np.dot(query_emb, desc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(desc_emb)))

        final_score = 0.6 * desc_score + 0.4 * img_score
        if final_score > threshold:
            results.append(
                {
                    'item_id': item['item_id'],
                    'filename': item['image_url'],
                    'image_url': item['image_url'],
                    'description': item['description'],
                    'score': final_score,
                    'status': item['status'],
                    'claimed_by': item['claimed_by'],
                    'expires_at': item['expires_at'],
                    'uploaded_at': item['created_at'],
                }
            )

    results.sort(key=lambda x: x['score'], reverse=True)
    return results


def collect_found_item(
    image_url: str,
    imgtaken_timestamp: float,
    box_id: Optional[int],
    finder_id: Optional[int] = None
) -> int:
    created_at = datetime.fromtimestamp(imgtaken_timestamp).isoformat()
    item_id = add_found_item(
        image_url=image_url,
        image_embedding=None,
        description='',
        description_embedding=None,
        status='collected',
        finder_user_id=finder_id,
        finder_img_url=image_url,
        created_at=created_at
    )

    if finder_id:
        try:
            update_finder_stats(finder_id, items_found_increment=1)
        except Exception as exc:  # pragma: no cover - best effort logging
            logger.warning("Unable to update finder stats: %s", exc)

    if box_id is not None:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO CASES (box_id, item_id, status, created_at)
                VALUES (?, ?, ?, ?)
                ''',
                (box_id, item_id, 'collected', created_at),
            )
            conn.commit()

    return item_id


def get_collected_items() -> Iterable[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ITEMS WHERE status = 'collected' ORDER BY created_at DESC")
        return [_serialise_item(row) for row in cursor.fetchall()]


def clear_all_items() -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ITEMS')
        conn.commit()
        return cursor.rowcount


# ---------------------------------------------------------------------------
# Box helpers
# ---------------------------------------------------------------------------

def add_box(location: str, status: bool = True, door_status: bool = False, load: int = 0) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO BOXES (status, location, load, door_status, last_accessed)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (1 if status else 0, location, load, 1 if door_status else 0, datetime.now().isoformat()),
        )
        conn.commit()
        return cursor.lastrowid


def delete_box(box_id: int) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM BOXES WHERE box_id = ?', (box_id,))
        conn.commit()
        return cursor.rowcount


def update_box(
    box_id: int,
    status: Optional[bool] = None,
    door_status: Optional[bool] = None,
    location: Optional[str] = None,
    load: Optional[int] = None
) -> int:
    fields = []
    values: list[Any] = []

    if status is not None:
        fields.append('status = ?')
        values.append(1 if status else 0)
    if door_status is not None:
        fields.append('door_status = ?')
        values.append(1 if door_status else 0)
    if location is not None:
        fields.append('location = ?')
        values.append(location)
    if load is not None:
        fields.append('load = ?')
        values.append(load)

    if not fields:
        return 0

    fields.append('last_accessed = ?')
    values.append(datetime.now().isoformat())
    values.append(box_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE BOXES SET {', '.join(fields)} WHERE box_id = ?",
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount


def get_box_status(box_id: int) -> Optional[sqlite3.Row]:
    return _fetch_one('SELECT * FROM BOXES WHERE box_id = ?', (box_id,))


def update_box_status(
    box_id: int,
    status: Optional[str] = None,
    current_load: Optional[int] = None,
    door_status: Optional[str] = None,
    capacity: Optional[int] = None
) -> int:
    fields = []
    values: list[Any] = []

    if status is not None:
        fields.append('status = ?')
        values.append(1 if status in (True, 'available') else 0)
    if current_load is not None:
        fields.append('load = ?')
        values.append(current_load)
    if door_status is not None:
        fields.append('door_status = ?')
        values.append(1 if door_status in (True, 'open') else 0)
    if capacity is not None:
        # Backwards compatibility – treat capacity as load cap using load column
        fields.append('load = ?')
        values.append(capacity)

    if not fields:
        return 0

    fields.append('last_accessed = ?')
    values.append(datetime.now().isoformat())
    values.append(box_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE BOXES SET {', '.join(fields)} WHERE box_id = ?",
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount


def get_all_boxes() -> Iterable[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM BOXES ORDER BY box_id')
        return cursor.fetchall()


# ---------------------------------------------------------------------------
# Case helpers
# ---------------------------------------------------------------------------

def add_case(
    box_id: int,
    receiver_id: Optional[int] = None,
    receiver_image_url: Optional[str] = None,
    item_id: Optional[int] = None,
    status: str = 'available',
    case_close_at: Optional[str] = None
) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO CASES (
                box_id, receiver_image_url, receiver_id, item_id, status, case_close_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
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
    found_id: int,
    box_id: Optional[int] = None,
    receiver_id: Optional[int] = None,
    receiver_image_url: Optional[str] = None,
    item_id: Optional[int] = None,
    status: Optional[str] = None,
    case_close_at: Optional[str] = None
) -> int:
    fields = []
    values: list[Any] = []

    if box_id is not None:
        fields.append('box_id = ?')
        values.append(box_id)
    if receiver_id is not None:
        fields.append('receiver_id = ?')
        values.append(receiver_id)
    if receiver_image_url is not None:
        fields.append('receiver_image_url = ?')
        values.append(receiver_image_url)
    if item_id is not None:
        fields.append('item_id = ?')
        values.append(item_id)
    if status is not None:
        fields.append('status = ?')
        values.append(status)
    if case_close_at is not None:
        fields.append('case_close_at = ?')
        values.append(case_close_at)

    if not fields:
        return 0

    values.append(found_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE CASES SET {', '.join(fields)} WHERE found_id = ?",
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount


def delete_case(case_id: int) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM CASES WHERE found_id = ?', (case_id,))
        conn.commit()
        return cursor.rowcount


def get_case(case_id: int) -> Optional[sqlite3.Row]:
    return _fetch_one('SELECT * FROM CASES WHERE found_id = ?', (case_id,))


def get_all_case() -> Iterable[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM CASES ORDER BY found_id')
        return cursor.fetchall()


# Ensure the database is ready when the module is imported
init_database()
