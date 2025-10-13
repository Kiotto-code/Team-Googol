import sqlite3
import json
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging
import numpy as np

# Use absolute path to ensure consistent database location
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lost_and_found.db')
CLAIM_DURATION_MINUTES = 60

def init_database():
    """Create the new normalized schema and migrate any legacy data."""
    with sqlite3.connect(DATABASE_PATH, timeout=15.0) as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA busy_timeout=15000;')
        conn.execute('PRAGMA foreign_keys=ON;')

        _create_base_schema(conn)
        _migrate_legacy_schema(conn)

        conn.commit()


def _create_base_schema(conn: sqlite3.Connection) -> None:
    """Create the User, Item, Box, and Case tables if they don't exist."""
    cursor = conn.cursor()

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS User (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            rfid_tag TEXT UNIQUE,
            student_id TEXT UNIQUE,
            user_type TEXT NOT NULL DEFAULT 'both',
            items_found INTEGER NOT NULL DEFAULT 0,
            items_claimed INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_active DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS Box (
            box_id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL DEFAULT 'available',
            door_status TEXT NOT NULL DEFAULT 'closed',
            capacity INTEGER NOT NULL DEFAULT 1,
            current_load INTEGER NOT NULL DEFAULT 0,
            location TEXT,
            last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS Item (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            description TEXT,
            image_embedding TEXT,
            description_embedding TEXT,
            status TEXT NOT NULL DEFAULT 'available',
            claimed_at DATETIME,
            claimed_user_id INTEGER,
            finder_user_id INTEGER,
            uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            box_id INTEGER,
            imgtaken_timestamp REAL,
            FOREIGN KEY (claimed_user_id) REFERENCES User (user_id) ON DELETE SET NULL,
            FOREIGN KEY (finder_user_id) REFERENCES User (user_id) ON DELETE SET NULL,
            FOREIGN KEY (box_id) REFERENCES Box (box_id) ON DELETE SET NULL
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS "Case" (
            case_id INTEGER PRIMARY KEY AUTOINCREMENT,
            box_id INTEGER NOT NULL,
            reciver_id INTEGER,
            receiver_image_url TEXT,
            item_id INTEGER,
            status TEXT NOT NULL DEFAULT 'available',
            case_close_at DATETIME,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (box_id) REFERENCES Box (box_id) ON DELETE CASCADE,
            FOREIGN KEY (reciver_id) REFERENCES User (user_id) ON DELETE SET NULL,
            FOREIGN KEY (item_id) REFERENCES Item (item_id) ON DELETE SET NULL
        )
        '''
    )


def _table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _migrate_legacy_schema(conn: sqlite3.Connection) -> None:
    """Migrate data from legacy tables into the new normalized schema."""
    cursor = conn.cursor()

    _migrate_users(cursor)
    _migrate_boxes(cursor)
    _migrate_items(cursor)
    _migrate_cases(cursor)


def _migrate_users(cursor: sqlite3.Cursor) -> None:
    cursor.execute('SELECT COUNT(*) FROM User')
    if cursor.fetchone()[0] > 0:
        return

    migrated_rows = 0

    if _table_exists(cursor, 'USERS'):
        cursor.execute('SELECT * FROM USERS')
        for row in cursor.fetchall():
            cursor.execute(
                '''
                INSERT OR IGNORE INTO User (
                    user_id, name, email, phone, rfid_tag, student_id,
                    user_type, items_found, items_claimed, created_at, last_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    row['user_id'],
                    row['name'],
                    row['email'],
                    row['phone'],
                    row['rfid_tag'],
                    row['student_id'],
                    row['user_type'] if row['user_type'] else 'both',
                    row['items_found'] if row['items_found'] is not None else 0,
                    row['items_claimed'] if row['items_claimed'] is not None else 0,
                    row['created_at'],
                    row['last_active'],
                ),
            )
            migrated_rows += 1

    legacy_sources = (
        ('FINDERS', 'finder', 'rfid_tag'),
        ('COLLECTORS', 'collector', 'student_id'),
    )

    for table_name, user_type, id_column in legacy_sources:
        if not _table_exists(cursor, table_name):
            continue

        cursor.execute(f'SELECT * FROM {table_name}')
        for row in cursor.fetchall():
            data = {key: row[key] for key in row.keys()}
            cursor.execute(
                '''
                INSERT OR IGNORE INTO User (name, email, phone, rfid_tag, student_id, user_type, created_at, last_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    data.get('name'),
                    data.get('email'),
                    data.get('phone'),
                    data.get('rfid_tag') if id_column == 'rfid_tag' else None,
                    data.get('student_id') if id_column == 'student_id' else None,
                    user_type,
                    data.get('created_at', datetime.now().isoformat()),
                    data.get('last_active', datetime.now().isoformat()),
                ),
            )
            migrated_rows += 1

    if migrated_rows:
        print(f"Migrated {migrated_rows} legacy users into User table")


def _migrate_boxes(cursor: sqlite3.Cursor) -> None:
    cursor.execute('SELECT COUNT(*) FROM Box')
    if cursor.fetchone()[0] > 0:
        return

    if not _table_exists(cursor, 'BOXES'):
        return

    cursor.execute('SELECT * FROM BOXES')
    for row in cursor.fetchall():
        row_dict = {key: row[key] for key in row.keys()}

        status_value = row_dict.get('status')
        if isinstance(status_value, (int, float)):
            status = 'available' if status_value else 'unavailable'
        else:
            status = str(status_value) if status_value is not None else 'available'

        door_status_value = row_dict.get('door_status')
        if isinstance(door_status_value, (int, float)):
            door_status = 'open' if door_status_value else 'closed'
        else:
            door_status = str(door_status_value) if door_status_value is not None else 'closed'

        cursor.execute(
            '''
            INSERT OR IGNORE INTO Box (
                box_id, status, door_status, capacity, current_load, location, last_updated
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                row_dict.get('box_id'),
                status,
                door_status,
                row_dict.get('capacity', 1),
                row_dict.get('load', 0),
                row_dict.get('location'),
                row_dict.get('last_accessed', datetime.now().isoformat()),
            ),
        )


def _migrate_items(cursor: sqlite3.Cursor) -> None:
    cursor.execute('SELECT COUNT(*) FROM Item')
    if cursor.fetchone()[0] > 0:
        return

    if _table_exists(cursor, 'FOUND_ITEMS'):
        cursor.execute('SELECT * FROM FOUND_ITEMS')
        for row in cursor.fetchall():
            row_dict = {key: row[key] for key in row.keys()}
            cursor.execute(
                '''
                INSERT OR IGNORE INTO Item (
                    item_id, filename, description, image_embedding, description_embedding,
                    status, claimed_at, claimed_user_id, finder_user_id, uploaded_at, expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    row_dict.get('id'),
                    row_dict.get('filename'),
                    row_dict.get('description'),
                    row_dict.get('image_embedding'),
                    row_dict.get('description_embedding'),
                    row_dict.get('status'),
                    row_dict.get('claimed_at'),
                    row_dict.get('claimed_by'),
                    row_dict.get('finder_id'),
                    row_dict.get('uploaded_at'),
                    row_dict.get('expires_at'),
                ),
            )

    if _table_exists(cursor, 'COLLECTED_ITEMS'):
        cursor.execute('SELECT * FROM COLLECTED_ITEMS')
        for row in cursor.fetchall():
            row_dict = {key: row[key] for key in row.keys()}
            cursor.execute(
                '''
                INSERT OR IGNORE INTO Item (
                    filename, status, finder_user_id, uploaded_at, box_id, imgtaken_timestamp
                )
                VALUES (?, 'collected', ?, ?, ?, ?)
                ''',
                (
                    row_dict.get('filename'),
                    row_dict.get('finder_id'),
                    row_dict.get('uploaded_at'),
                    row_dict.get('box_id'),
                    row_dict.get('imgtaken_timestamp'),
                ),
            )


def _migrate_cases(cursor: sqlite3.Cursor) -> None:
    cursor.execute('SELECT COUNT(*) FROM "Case"')
    if cursor.fetchone()[0] > 0:
        return

    if not _table_exists(cursor, 'CASES'):
        return

    cursor.execute('SELECT * FROM CASES')
    for row in cursor.fetchall():
        row_dict = {key: row[key] for key in row.keys()}
        cursor.execute(
            '''
            INSERT OR IGNORE INTO "Case" (
                case_id, box_id, reciver_id, receiver_image_url, item_id, status, case_close_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                row_dict.get('found_id'),
                row_dict.get('box_id'),
                row_dict.get('receiver_id'),
                row_dict.get('receiver_image_url'),
                row_dict.get('item_id'),
                row_dict.get('status'),
                row_dict.get('case_close_at'),
                row_dict.get('created_at'),
            ),
        )

@contextmanager
def get_db_connection():
    """Context manager for database connections with better concurrency.
    - WAL journal mode improves read/write concurrency
    - busy_timeout and connect timeout reduce 'database is locked' errors
    """
    conn = sqlite3.connect(DATABASE_PATH, timeout=15.0)
    try:
        # Concurrency-friendly pragmas
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA busy_timeout=15000;')
        conn.execute('PRAGMA foreign_keys=ON;')
        conn.row_factory = sqlite3.Row  # This enables column access by name
        yield conn
    finally:
        conn.close()

def add_found_item(
    filename,
    image_embedding=None,
    description="",
    description_embedding=None,
    *,
    finder_user_id=None,
    box_id=None,
    imgtaken_timestamp=None,
    status=None,
):
    """Add a found item to the Item table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        img_emb_json = json.dumps(image_embedding) if image_embedding is not None else None
        desc_emb_json = json.dumps(description_embedding) if description_embedding is not None else None

        columns = [
            'filename',
            'description',
            'image_embedding',
            'description_embedding',
            'finder_user_id',
            'box_id',
            'imgtaken_timestamp',
        ]
        values = [
            filename,
            description,
            img_emb_json,
            desc_emb_json,
            finder_user_id,
            box_id,
            imgtaken_timestamp,
        ]

        if status is not None:
            columns.append('status')
            values.append(status)

        placeholders = ', '.join('?' for _ in columns)
        cursor.execute(
            f"INSERT INTO Item ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )

        conn.commit()
        return cursor.lastrowid

def _fetch_case_item_rows(where_clause: str = '', params: tuple = ()):  # pragma: no cover - simple helper
    base_query = '''
        SELECT
            i.item_id AS item_id,
            i.filename AS filename,
            i.description AS description,
            i.status AS item_status,
            i.claimed_at AS claimed_at,
            i.expires_at AS item_expires_at,
            i.uploaded_at AS uploaded_at,
            i.claimed_user_id AS claimed_user_id,
            c.case_id AS case_id,
            c.box_id AS box_id,
            c.reciver_id AS reciver_id,
            c.status AS case_status,
            c.case_close_at AS case_close_at,
            c.created_at AS case_created_at
        FROM Item i
        LEFT JOIN "Case" c ON c.item_id = i.item_id
    '''

    if where_clause:
        base_query += f" {where_clause}"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(base_query, params)
        return cursor.fetchall()


def _is_timestamp_past(value) -> bool:
    if not value:
        return False
    try:
        return datetime.fromisoformat(value) <= datetime.now()
    except ValueError:
        return False


def _map_case_item_status(case_status, item_status, case_close_at, item_expires_at):
    if case_status:
        if case_status == 'available_to_claim':
            return 'available'
        if case_status == 'claimed' and _is_timestamp_past(case_close_at):
            return 'available'
        return str(case_status)

    if item_status:
        if item_status == 'claimed':
            if _is_timestamp_past(item_expires_at):
                return 'available'
            return 'claimed'
        return str(item_status)

    return 'available'


def _normalize_case_item_row(row):
    if row is None:
        return None

    status = _map_case_item_status(
        row['case_status'],
        row['item_status'],
        row['case_close_at'],
        row['item_expires_at'],
    )

    claimed_by = row['reciver_id'] or row['claimed_user_id']
    claimed_at = row['claimed_at']
    expires_at = row['case_close_at'] or row['item_expires_at']

    if status == 'available' and (
        (row['case_status'] == 'claimed' and _is_timestamp_past(row['case_close_at']))
        or (row['case_status'] is None and row['item_status'] == 'claimed' and _is_timestamp_past(row['item_expires_at']))
    ):
        claimed_by = None
        claimed_at = None
        expires_at = None

    return {
        'id': row['item_id'],
        'item_id': row['item_id'],
        'case_id': row['case_id'],
        'filename': row['filename'],
        'description': row['description'],
        'status': status,
        'claimed_by': claimed_by,
        'claimed_at': claimed_at,
        'expires_at': expires_at,
        'uploaded_at': row['uploaded_at'],
        'case_status': row['case_status'],
        'case_close_at': row['case_close_at'],
        'box_id': row['box_id'],
    }


def get_items_with_case():
    """Return normalized items joined with their cases."""
    rows = _fetch_case_item_rows('ORDER BY i.uploaded_at DESC')
    return [_normalize_case_item_row(row) for row in rows]


def get_all_items():
    """Backwards-compatible wrapper returning all items with case data."""
    return get_items_with_case()


def get_available_items():
    """Get all items that are available for claiming."""
    return [item for item in get_items_with_case() if item and item.get('status') == 'available']


def claim_item(item_id, claimed_by_collector_id):
    """Claim an item for 1 hour by collector ID, updating related cases."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            '''
            SELECT
                i.status AS item_status,
                i.expires_at AS item_expires_at,
                c.case_id AS case_id,
                c.status AS case_status,
                c.case_close_at AS case_close_at
            FROM Item i
            LEFT JOIN "Case" c ON c.item_id = i.item_id
            WHERE i.item_id = ?
            ORDER BY c.case_id DESC
            LIMIT 1
            ''',
            (item_id,),
        )
        result = cursor.fetchone()
        if not result:
            return False, "Item not found"

        item_status = result['item_status']
        item_expires_at = result['item_expires_at']
        case_id = result['case_id']
        case_status = result['case_status']
        case_close_at = result['case_close_at']

        if case_id:
            if case_status == 'retrieved':
                return False, "Item is no longer available"
            if case_status == 'claimed' and not _is_timestamp_past(case_close_at):
                return False, "Item is currently claimed"
            if case_status not in (None, 'available_to_claim', 'available', 'claimed'):
                return False, f"Item cannot be claimed while case is {case_status}"
        else:
            if item_status == 'claimed' and not _is_timestamp_past(item_expires_at):
                return False, "Item is currently claimed"
            if item_status not in (None, 'available', 'claimed'):
                return False, f"Item cannot be claimed while status is {item_status}"

        claimed_at = datetime.now()
        claim_expires_at = (claimed_at + timedelta(minutes=CLAIM_DURATION_MINUTES)).isoformat()
        claimed_at_iso = claimed_at.isoformat()

        cursor.execute(
            '''
            UPDATE Item
            SET status = 'claimed',
                claimed_at = ?,
                claimed_user_id = ?,
                expires_at = ?
            WHERE item_id = ?
            ''',
            (
                claimed_at_iso,
                claimed_by_collector_id,
                claim_expires_at,
                item_id,
            ),
        )

        if case_id:
            cursor.execute(
                '''
                UPDATE "Case"
                SET status = 'claimed',
                    case_close_at = ?,
                    reciver_id = ?
                WHERE case_id = ?
                ''',
                (
                    claim_expires_at,
                    claimed_by_collector_id,
                    case_id,
                ),
            )

        conn.commit()

        try:
            update_collector_stats(claimed_by_collector_id, items_claimed_increment=1)
        except Exception as e:
            print(f"Warning: update_collector_stats skipped due to: {e}")
        return True, "Item claimed successfully"


def release_expired_claims():
    """Release claims that have expired for both legacy items and new cases."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()

        cursor.execute(
            '''
            SELECT case_id, item_id FROM "Case"
            WHERE status = 'claimed'
              AND case_close_at IS NOT NULL
              AND datetime(case_close_at) < datetime(?)
            ''',
            (current_time,),
        )
        expired_rows = cursor.fetchall()

        case_ids = {row['case_id'] for row in expired_rows if row['case_id'] is not None}
        item_ids = {row['item_id'] for row in expired_rows if row['item_id'] is not None}

        if case_ids:
            placeholders = ', '.join('?' for _ in case_ids)
            cursor.execute(
                f'''
                UPDATE "Case"
                SET status = 'available_to_claim',
                    case_close_at = NULL,
                    reciver_id = NULL
                WHERE case_id IN ({placeholders})
                ''',
                tuple(case_ids),
            )

        released_count = len(case_ids)

        if item_ids:
            placeholders = ', '.join('?' for _ in item_ids)
            cursor.execute(
                f'''
                UPDATE Item
                SET status = 'available',
                    claimed_at = NULL,
                    claimed_user_id = NULL,
                    expires_at = NULL
                WHERE item_id IN ({placeholders})
                ''',
                tuple(item_ids),
            )

        cursor.execute(
            '''
            UPDATE Item
            SET status = 'available',
                claimed_at = NULL,
                claimed_user_id = NULL,
                expires_at = NULL
            WHERE status = 'claimed'
              AND expires_at IS NOT NULL
              AND datetime(expires_at) < datetime(?)
              AND item_id NOT IN (
                    SELECT item_id FROM "Case" WHERE item_id IS NOT NULL
                )
            ''',
            (current_time,),
        )

        legacy_count = cursor.rowcount
        conn.commit()
        return released_count + legacy_count

def delete_item(filename):
    """Delete an item from the Item table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Item WHERE filename = ?', (filename,))
        conn.commit()
        return cursor.rowcount > 0

def get_item_by_filename(filename):
    """Get an item by filename."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Item WHERE filename = ?', (filename,))
        return cursor.fetchone()

def search_items(query_embedding, threshold=0.4):
    """Search for items based on embedding similarity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        cursor.execute(
            '''
            SELECT * FROM Item
            WHERE status = 'available'
               OR (status = 'claimed' AND expires_at IS NOT NULL AND datetime(expires_at) < datetime(?))
            ''',
            (current_time,),
        )

        items = cursor.fetchall()
        results = []

        query_emb = np.array(query_embedding, dtype=np.float32)

        for item in items:
            image_data = item['image_embedding']
            if not image_data:
                continue

            img_emb = np.array(json.loads(image_data), dtype=np.float32)
            denom = np.linalg.norm(query_emb) * np.linalg.norm(img_emb)
            if denom == 0:
                continue
            img_score = float(np.dot(query_emb, img_emb) / denom)

            desc_score = 0.0
            if item['description_embedding']:
                desc_emb = np.array(json.loads(item['description_embedding']), dtype=np.float32)
                desc_denom = np.linalg.norm(query_emb) * np.linalg.norm(desc_emb)
                if desc_denom != 0:
                    desc_score = float(np.dot(query_emb, desc_emb) / desc_denom)

            final_score = (0.6 * desc_score + 0.4 * img_score)

            if final_score > threshold:
                status = item['status']
                expires_at = item['expires_at']
                if status == 'claimed' and expires_at:
                    expires_datetime = datetime.fromisoformat(expires_at)
                    if datetime.now() > expires_datetime:
                        release_expired_claims()
                        status = 'available'

                results.append(
                    {
                        'item_id': item['item_id'],
                        'filename': item['filename'],
                        'description': item['description'],
                        'score': final_score,
                        'status': status,
                        'claimed_user_id': item['claimed_user_id'],
                        'expires_at': item['expires_at'],
                        'uploaded_at': item['uploaded_at'],
                    }
                )

        return results



# COLLECT
def collect_found_item(filename, imgtaken_timestamp, box_id, finder_user_id=None):
    """Collect a found item and store it as an Item entry."""
    item_id = add_found_item(
        filename,
        image_embedding=None,
        description="",
        description_embedding=None,
        finder_user_id=finder_user_id,
        box_id=box_id,
        imgtaken_timestamp=imgtaken_timestamp,
        status='collected',
    )

    if finder_user_id:
        update_finder_stats(finder_user_id, items_found_increment=1)

    return item_id


def get_collected_items():
    """Get all collected items."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM Item WHERE status = 'collected' ORDER BY uploaded_at DESC"
        )
        return cursor.fetchall()


def clear_all_items():
    """Clear all items from the Item table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Item")
        conn.commit()
        return cursor.rowcount

# USER MANAGEMENT - Unified User table helpers


def _resolve_phone_value(phone=None, phone_number=None):
    """Prefer the explicit phone_number field when supplied."""
    if phone_number is not None and str(phone_number).strip():
        return phone_number
    return phone


def _normalize_user_type(user_type: str | None) -> str:
    if not user_type:
        return 'both'
    normalized = str(user_type).strip().lower()
    if normalized not in {'finder', 'collector', 'both'}:
        return 'both'
    return normalized


def add_user(
    name,
    email=None,
    phone=None,
    rfid_tag=None,
    student_id=None,
    user_type='both',
    *,
    phone_number=None,
):
    """Add a new user to the system."""
    now = datetime.now().isoformat()
    phone_value = _resolve_phone_value(phone, phone_number)
    normalized_type = _normalize_user_type(user_type)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO User (name, email, phone, rfid_tag, student_id, user_type, created_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (name, email, phone_value, rfid_tag, student_id, normalized_type, now, now),
        )
        conn.commit()
        return cursor.lastrowid


def add_finder(name, email=None, phone=None, rfid_tag=None, *, phone_number=None):
    """Backward compatibility helper for creating finder users."""
    return add_user(
        name,
        email,
        phone,
        rfid_tag,
        None,
        'finder',
        phone_number=phone_number,
    )


def add_collector(name, email=None, phone=None, student_id=None, *, phone_number=None, id_number=None):
    """Backward compatibility helper for creating collector users."""
    student_identifier = student_id if student_id is not None else id_number
    return add_user(
        name,
        email,
        phone,
        None,
        student_identifier,
        'collector',
        phone_number=phone_number,
    )


def get_user_by_id(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE user_id = ?', (user_id,))
        return cursor.fetchone()


def get_user_by_email(email):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE email = ?', (email,))
        return cursor.fetchone()


def get_user_by_rfid(rfid_tag):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE rfid_tag = ?', (rfid_tag,))
        return cursor.fetchone()


def get_user_by_student_id(student_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE student_id = ?', (student_id,))
        return cursor.fetchone()


def _role_clause(role: str) -> tuple[str, tuple]:
    normalized = _normalize_user_type(role)
    if normalized == 'finder':
        return "user_type IN ('finder', 'both')", tuple()
    if normalized == 'collector':
        return "user_type IN ('collector', 'both')", tuple()
    if normalized == 'both':
        return "user_type = 'both'", tuple()
    raise ValueError(f"Unsupported role: {role}")


def user_has_role(user_row, role: str) -> bool:
    if user_row is None:
        return False

    if isinstance(user_row, dict):
        user_type = user_row.get('user_type')
    else:
        user_type = user_row['user_type']

    normalized = _normalize_user_type(user_type)
    target = _normalize_user_type(role)

    if target == 'finder':
        return normalized in {'finder', 'both'}
    if target == 'collector':
        return normalized in {'collector', 'both'}
    if target == 'both':
        return normalized == 'both'
    return False


def get_all_users(role: str | None = None):
    """Retrieve all users, optionally filtering by role."""
    base_query = "SELECT * FROM User"
    params: tuple = tuple()

    if role:
        clause, params = _role_clause(role)
        base_query = f"{base_query} WHERE {clause}"

    query = f"{base_query} ORDER BY created_at DESC"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def count_users_by_role(role: str) -> int:
    clause, params = _role_clause(role)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM User WHERE {clause}", params)
        result = cursor.fetchone()
        return int(result[0]) if result else 0


def get_finder_by_id(finder_id):
    return get_user_by_id(finder_id)


def get_collector_by_id(collector_id):
    return get_user_by_id(collector_id)


def get_finder_by_email(email):
    return get_user_by_email(email)


def get_collector_by_email(email):
    return get_user_by_email(email)


def get_finder_by_rfid(rfid_tag):
    return get_user_by_rfid(rfid_tag)


def get_collector_by_student_id(student_id):
    return get_user_by_student_id(student_id)


def update_user_stats(user_id, items_found_increment=0, items_claimed_increment=0):
    """Update aggregate counters for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            UPDATE User
            SET items_found = items_found + ?,
                items_claimed = items_claimed + ?,
                last_active = ?
            WHERE user_id = ?
            ''',
            (items_found_increment, items_claimed_increment, datetime.now().isoformat(), user_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_finder_stats(finder_id, items_found_increment=0, reputation_increment=0):
    return update_user_stats(finder_id, items_found_increment, 0)


def update_collector_stats(collector_id, items_claimed_increment=0, verification_status=None):
    return update_user_stats(collector_id, 0, items_claimed_increment)


def get_all_finders():
    return get_all_users('finder')


def get_all_collectors():
    return get_all_users('collector')


# BOX MANAGEMENT


def _status_to_storage(status):
    if isinstance(status, str):
        return status
    return 'available' if status else 'unavailable'


def _door_to_storage(door_status):
    if isinstance(door_status, str):
        return door_status
    return 'open' if door_status else 'closed'


def _normalize_box_row(row):
    if row is None:
        return None
    data = dict(row)
    status_value = str(data.get('status', '')).lower()
    data['status'] = 1 if status_value in {'1', 'true', 'available', 'open'} else 0
    door_value = str(data.get('door_status', '')).lower()
    data['door_status'] = 1 if door_value in {'1', 'true', 'open'} else 0
    data['load'] = data.get('current_load', data.get('load', 0))
    data.setdefault('current_load', data['load'])
    if 'last_updated' in data and 'last_accessed' not in data:
        data['last_accessed'] = data['last_updated']
    return data


def add_box(location, status=True, door_status=False, load=0, capacity=1):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO Box (status, door_status, capacity, current_load, location, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                _status_to_storage(status),
                _door_to_storage(door_status),
                capacity,
                load,
                location,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def delete_box(box_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Box WHERE box_id = ?', (box_id,))
        conn.commit()
        return cursor.rowcount


def update_box(box_id, status=None, door_status=None, location=None, load=None):
    fields = []
    values = []
    if status is not None:
        fields.append('status = ?')
        values.append(_status_to_storage(status))
    if door_status is not None:
        fields.append('door_status = ?')
        values.append(_door_to_storage(door_status))
    if location is not None:
        fields.append('location = ?')
        values.append(location)
    if load is not None:
        fields.append('current_load = ?')
        values.append(load)

    if not fields:
        return 0

    fields.append('last_updated = ?')
    values.append(datetime.now().isoformat())
    values.append(box_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE Box SET {', '.join(fields)} WHERE box_id = ?",
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount


def get_box_status(box_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Box WHERE box_id = ?', (box_id,))
        row = cursor.fetchone()
        return _normalize_box_row(row)


def update_box_status(box_id, status=None, current_load=None, door_status=None, capacity=None):
    fields = []
    values = []
    if status is not None:
        fields.append('status = ?')
        values.append(status if isinstance(status, str) else _status_to_storage(status))
    if current_load is not None:
        fields.append('current_load = ?')
        values.append(current_load)
    if door_status is not None:
        fields.append('door_status = ?')
        values.append(door_status if isinstance(door_status, str) else _door_to_storage(door_status))
    if capacity is not None:
        fields.append('capacity = ?')
        values.append(capacity)

    if not fields:
        return 0

    fields.append('last_updated = ?')
    values.append(datetime.now().isoformat())
    values.append(box_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE Box SET {', '.join(fields)} WHERE box_id = ?",
            tuple(values),
        )
        conn.commit()
        return cursor.rowcount


def get_all_boxes():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Box ORDER BY box_id')
        rows = cursor.fetchall()
        return [_normalize_box_row(row) for row in rows]


# CASE MANAGEMENT


def add_case(box_id, reciver_id=None, receiver_image_url=None, item_id=None, status='available', case_close_at=None, receiver_id=None):
    if reciver_id is None and receiver_id is not None:
        reciver_id = receiver_id

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO "Case" (box_id, reciver_id, receiver_image_url, item_id, status, case_close_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                box_id,
                reciver_id,
                receiver_image_url,
                item_id,
                status,
                case_close_at,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def update_case(case_id=None, *, found_id=None, box_id=None, reciver_id=None, receiver_id=None, receiver_image_url=None, item_id=None, status=None, case_close_at=None):
    target_id = case_id if case_id is not None else found_id
    if target_id is None:
        raise ValueError('case_id is required')

    if reciver_id is None and receiver_id is not None:
        reciver_id = receiver_id

    fields = []
    values = []
    if box_id is not None:
        fields.append('box_id = ?')
        values.append(box_id)
    if reciver_id is not None:
        fields.append('reciver_id = ?')
        values.append(reciver_id)
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

    values.append(target_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        sql = f'UPDATE "Case" SET {", ".join(fields)} WHERE case_id = ?'
        cursor.execute(sql, tuple(values))
        conn.commit()
        return cursor.rowcount


def delete_case(case_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM "Case" WHERE case_id = ?', (case_id,))
        conn.commit()
        return cursor.rowcount


def get_case(case_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "Case" WHERE case_id = ?', (case_id,))
        return cursor.fetchone()


def get_all_case():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "Case" ORDER BY case_id')
        return cursor.fetchall()

# Database is initialized when needed - removed automatic initialization
