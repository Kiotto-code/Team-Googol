import sqlite3
import json
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging
import numpy as np

# Use absolute path to ensure consistent database location
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lost_and_found.db')

def init_database():
    """Initialize the database with the required tables."""
    with sqlite3.connect(DATABASE_PATH, timeout=15.0) as conn:
        cursor = conn.cursor()
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('PRAGMA busy_timeout=15000;')
        cursor.execute('PRAGMA foreign_keys=ON;')
        
        # Initialize unified USERS table
        init_users_table()
        init_boxes_table()
        
        # Create FOUND_ITEMS table for found items (renamed from CASE to avoid SQL reserved word)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS FOUND_ITEMS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                description TEXT,
                image_embedding TEXT NOT NULL,
                description_embedding TEXT,
                status TEXT DEFAULT 'available',
                claimed_at DATETIME,
                claimed_by INTEGER,  -- References USERS.user_id
                finder_id INTEGER,   -- References USERS.user_id 
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                FOREIGN KEY (claimed_by) REFERENCES USERS (user_id),
                FOREIGN KEY (finder_id) REFERENCES USERS (user_id)
            )
        ''')
        
        # Create COLLECTED_ITEMS table for items collected by collection system
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS COLLECTED_ITEMS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                box_id TEXT,
                finder_id INTEGER,  -- References USERS.user_id (system or person who found it)
                imgtaken_timestamp REAL,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (finder_id) REFERENCES USERS (user_id)
            )
        ''')
        
        # Add migration for existing columns if needed
        migrate_user_references()
        
        conn.commit()

def migrate_user_references():
    """Migrate existing user references to new separated table structure."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if we need to migrate FOUND_ITEMS claimed_by from TEXT to INTEGER
        cursor.execute("PRAGMA table_info(FOUND_ITEMS)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        # Add finder_id column first if it doesn't exist
        if 'finder_id' not in columns:
            cursor.execute('ALTER TABLE FOUND_ITEMS ADD COLUMN finder_id INTEGER')
            print("Added finder_id column to FOUND_ITEMS")
            # Refresh columns info
            cursor.execute("PRAGMA table_info(FOUND_ITEMS)")
            columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        if 'claimed_by' in columns and 'TEXT' in columns['claimed_by']:
            print("Migrating FOUND_ITEMS claimed_by column...")
            # Add new column
            cursor.execute('ALTER TABLE FOUND_ITEMS ADD COLUMN claimed_by_temp INTEGER')
            # Copy numeric values only (ignore old text values)
            cursor.execute('''
                UPDATE FOUND_ITEMS 
                SET claimed_by_temp = CAST(claimed_by AS INTEGER) 
                WHERE claimed_by IS NOT NULL AND claimed_by != '' 
                AND claimed_by GLOB '[0-9]*'
            ''')
            # Create new table with proper structure
            cursor.execute('''CREATE TABLE FOUND_ITEMS_NEW AS 
                SELECT id, filename, description, image_embedding, description_embedding, 
                       status, claimed_at, claimed_by_temp as claimed_by, finder_id, 
                       uploaded_at, expires_at 
                FROM FOUND_ITEMS''')
            cursor.execute('DROP TABLE FOUND_ITEMS')
            cursor.execute('ALTER TABLE FOUND_ITEMS_NEW RENAME TO FOUND_ITEMS')
            print("Migrated FOUND_ITEMS claimed_by from TEXT to INTEGER")
        
        # Check COLLECTED_ITEMS for migration
        cursor.execute("PRAGMA table_info(COLLECTED_ITEMS)")
        collected_columns = {col[1]: col for col in cursor.fetchall()}
        
        if 'found_by_user_id' in collected_columns and 'finder_id' not in collected_columns:
            cursor.execute('ALTER TABLE COLLECTED_ITEMS ADD COLUMN finder_id INTEGER')
            cursor.execute('UPDATE COLLECTED_ITEMS SET finder_id = found_by_user_id WHERE found_by_user_id IS NOT NULL')
            print("Migrated COLLECTED_ITEMS found_by_user_id to finder_id")
        
        conn.commit()

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

def add_found_item(filename, image_embedding, description="", description_embedding=None):
    """Add a found item to the FOUND_ITEMS table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Convert embeddings to JSON strings for storage
        img_emb_json = json.dumps(image_embedding)
        desc_emb_json = json.dumps(description_embedding) if description_embedding else None
        
        cursor.execute('''
            INSERT INTO FOUND_ITEMS (filename, description, image_embedding, description_embedding)
            VALUES (?, ?, ?, ?)
        ''', (filename, description, img_emb_json, desc_emb_json))
        
        conn.commit()
        return cursor.lastrowid

def get_available_items():
    """Get all available (unclaimed) items."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        cursor.execute('''
            SELECT * FROM FOUND_ITEMS 
            WHERE status = 'available' OR (status = 'claimed' AND datetime(expires_at) < datetime(?))
        ''', (current_time,))
        return cursor.fetchall()

def get_all_items():
    """Get all items from the FOUND_ITEMS table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM FOUND_ITEMS')
        return cursor.fetchall()

def claim_item(item_id, claimed_by_collector_id):
    """Claim an item for 1 hour by collector ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if item is available
        cursor.execute('''
            SELECT status, expires_at FROM FOUND_ITEMS 
            WHERE id = ?
        ''', (item_id,))
        
        result = cursor.fetchone()
        if not result:
            return False, "Item not found"
        
        status, expires_at = result
        
        # Check if item is available or claim has expired
        if status == 'claimed' and expires_at:
            expires_datetime = datetime.fromisoformat(expires_at)
            if datetime.now() < expires_datetime:
                return False, "Item is currently claimed"
        
        # Claim the item
        claimed_at = datetime.now()
        expires_at = claimed_at + timedelta(minutes=1)
        
        cursor.execute('''
            UPDATE FOUND_ITEMS 
            SET status = 'claimed', claimed_at = ?, claimed_by = ?, expires_at = ?
            WHERE id = ?
        ''', (claimed_at.isoformat(), claimed_by_collector_id, expires_at.isoformat(), item_id))

        # Commit the item update first to release the write lock quickly
        conn.commit()

        # Update collector's last active timestamp and stats (best-effort, separate transaction)
        try:
            update_collector_stats(claimed_by_collector_id, items_claimed_increment=1)
        except Exception as e:
            # Do not fail the claim if stats update hits a transient lock
            print(f"Warning: update_collector_stats skipped due to: {e}")
        return True, "Item claimed successfully"

def release_expired_claims():
    """Release claims that have expired (older than 1 hour)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Use Python's current time instead of SQLite's UTC time for consistency
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE FOUND_ITEMS 
            SET status = 'available', claimed_at = NULL, claimed_by = NULL, expires_at = NULL
            WHERE status = 'claimed' AND datetime(expires_at) < datetime(?)
        ''', (current_time,))
        
        conn.commit()
        return cursor.rowcount

def delete_item(filename):
    """Delete an item from the FOUND_ITEMS table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM FOUND_ITEMS WHERE filename = ?', (filename,))
        conn.commit()
        return cursor.rowcount > 0

def get_item_by_filename(filename):
    """Get an item by filename."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM FOUND_ITEMS WHERE filename = ?', (filename,))
        return cursor.fetchone()

def search_items(query_embedding, threshold=0.4):
    """Search for items based on embedding similarity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get all available items
        current_time = datetime.now().isoformat()
        cursor.execute('''
            SELECT * FROM FOUND_ITEMS 
            WHERE status = 'available' OR (status = 'claimed' AND datetime(expires_at) < datetime(?))
        ''', (current_time,))
        
        items = cursor.fetchall()
        results = []
        
        query_emb = np.array(query_embedding, dtype=np.float32)
        
        for item in items:
            # Parse image embedding
            img_emb = np.array(json.loads(item['image_embedding']), dtype=np.float32)
            img_score = float(np.dot(query_emb, img_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(img_emb)))
            
            # Parse description embedding if available
            desc_score = 0.0
            if item['description_embedding']:
                desc_emb = np.array(json.loads(item['description_embedding']), dtype=np.float32)
                desc_score = float(np.dot(query_emb, desc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(desc_emb)))
            
            # Combine scores
            final_score = (0.6 * desc_score + 0.4 * img_score)
            
            if final_score > threshold:
                # Update status if claim expired
                if item['status'] == 'claimed' and item['expires_at']:
                    expires_datetime = datetime.fromisoformat(item['expires_at'])
                    if datetime.now() > expires_datetime:
                        release_expired_claims()  # Clean up expired claims
                        status = 'available'
                    else:
                        status = item['status']
                else:
                    status = item['status']
                
                results.append({
                    'id': item['id'],
                    'filename': item['filename'],
                    'description': item['description'],
                    'score': final_score,
                    'status': status,
                    'claimed_by': item['claimed_by'],
                    'expires_at': item['expires_at'],
                    'uploaded_at': item['uploaded_at']
                })
        
        return results


# COLLECT
def collect_found_item(filename, imgtaken_timestamp, box_id, finder_id=None):
    """Collect a found item and store in COLLECTED_ITEMS table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO COLLECTED_ITEMS (filename, imgtaken_timestamp, box_id, finder_id)
            VALUES (?, ?, ?, ?)
        ''', (filename, imgtaken_timestamp, box_id, finder_id))
        
        # Update finder stats if provided
        if finder_id:
            update_finder_stats(finder_id, items_found_increment=1)
            
        conn.commit()
        return cursor.lastrowid

def get_collected_items():
    """Get all collected items."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM COLLECTED_ITEMS ORDER BY uploaded_at DESC')
        return cursor.fetchall()

def clear_all_items():
    """Clear all items from the FOUND_ITEMS table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM FOUND_ITEMS')
        conn.commit()
        return cursor.rowcount

# USER MANAGEMENT - Unified USERS table
def init_users_table():
    """Initialize unified USERS table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS USERS (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                rfid_tag TEXT UNIQUE,
                student_id TEXT UNIQUE,
                user_type TEXT DEFAULT 'both',  -- 'finder', 'collector', 'both'
                items_found INTEGER DEFAULT 0,  -- Count of items they've found
                items_claimed INTEGER DEFAULT 0,  -- Count of items they've claimed
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Migrate from old FINDERS/COLLECTORS tables if they exist
        migrate_separated_tables_to_users()
        
        conn.commit()

def migrate_separated_tables_to_users():
    """Migrate existing FINDERS and COLLECTORS tables to unified USERS table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if old FINDERS table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='FINDERS'")
        has_finders = cursor.fetchone() is not None
        
        # Check if old COLLECTORS table exists  
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='COLLECTORS'")
        has_collectors = cursor.fetchone() is not None
        
        if has_finders or has_collectors:
            print("Migrating FINDERS and COLLECTORS tables to unified USERS table...")
            
            # Migrate FINDERS
            if has_finders:
                cursor.execute('SELECT * FROM FINDERS')
                finders = cursor.fetchall()
                for finder in finders:
                    finder_dict = dict(finder)
                    cursor.execute('''
                        INSERT OR IGNORE INTO USERS (name, email, phone, rfid_tag, user_type, created_at, last_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (finder_dict.get('name'), finder_dict.get('email'), finder_dict.get('phone'),
                          finder_dict.get('rfid_tag'), 'finder', 
                          finder_dict.get('created_at'), finder_dict.get('last_active')))
            
            # Migrate COLLECTORS
            if has_collectors:
                cursor.execute('SELECT * FROM COLLECTORS')
                collectors = cursor.fetchall()
                for collector in collectors:
                    collector_dict = dict(collector)
                    # Check if user already exists (in case they were both finder and collector)
                    cursor.execute('SELECT user_id FROM USERS WHERE email = ?', (collector_dict.get('email'),))
                    existing_user = cursor.fetchone()
                    
                    if existing_user:
                        # Update existing user to be 'both'
                        cursor.execute('''
                            UPDATE USERS SET user_type = 'both', student_id = ?
                            WHERE user_id = ?
                        ''', (collector_dict.get('student_id'), existing_user[0]))
                    else:
                        # Insert new collector
                        cursor.execute('''
                            INSERT OR IGNORE INTO USERS (name, email, phone, student_id, user_type, created_at, last_active)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (collector_dict.get('name'), collector_dict.get('email'), collector_dict.get('phone'),
                              collector_dict.get('student_id'), 'collector',
                              collector_dict.get('created_at'), collector_dict.get('last_active')))
            
            # Rename old tables for backup
            if has_finders:
                cursor.execute('ALTER TABLE FINDERS RENAME TO FINDERS_BACKUP')
                print("FINDERS table renamed to FINDERS_BACKUP")
            if has_collectors:
                cursor.execute('ALTER TABLE COLLECTORS RENAME TO COLLECTORS_BACKUP') 
                print("COLLECTORS table renamed to COLLECTORS_BACKUP")
            
            print("Migration to unified USERS table completed")
        
        conn.commit()

# USER management functions (unified)
def add_user(name, email=None, phone=None, rfid_tag=None, student_id=None, user_type='both'):
    """Add a new user to the system."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO USERS (name, email, phone, rfid_tag, student_id, user_type, created_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, rfid_tag, student_id, user_type,
              datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid

# Backward compatibility functions for existing code
def add_finder(name, email=None, phone=None, rfid_tag=None):
    """Add a new finder to the system (backward compatibility)."""
    return add_user(name, email, phone, rfid_tag, None, 'finder')

def add_collector(name, email=None, phone=None, student_id=None):
    """Add a new collector to the system (backward compatibility)."""
    return add_user(name, email, phone, None, student_id, 'collector')

def get_user_by_id(user_id):
    """Get user information by user ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM USERS WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

# Backward compatibility functions
def get_finder_by_id(finder_id):
    """Get finder information by ID (backward compatibility)."""
    return get_user_by_id(finder_id)

def get_collector_by_id(collector_id):
    """Get collector information by ID (backward compatibility)."""
    return get_user_by_id(collector_id)

def get_user_by_email(email):
    """Get user information by email."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM USERS WHERE email = ?', (email,))
        return cursor.fetchone()

# Backward compatibility functions
def get_finder_by_email(email):
    """Get finder information by email (backward compatibility)."""
    return get_user_by_email(email)

def get_collector_by_email(email):
    """Get collector information by email (backward compatibility)."""
    return get_user_by_email(email)

def get_user_by_rfid(rfid_tag):
    """Get user information by RFID tag."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM USERS WHERE rfid_tag = ?', (rfid_tag,))
        return cursor.fetchone()

# Backward compatibility function
def get_finder_by_rfid(rfid_tag):
    """Get finder information by RFID tag (backward compatibility)."""
    return get_user_by_rfid(rfid_tag)

def get_user_by_student_id(student_id):
    """Get user information by student ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM USERS WHERE student_id = ?', (student_id,))
        return cursor.fetchone()

# Backward compatibility function
def get_collector_by_student_id(student_id):
    """Get collector information by student ID (backward compatibility)."""
    return get_user_by_student_id(student_id)

def update_user_stats(user_id, items_found_increment=0, items_claimed_increment=0):
    """Update user statistics."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE USERS 
            SET items_found = items_found + ?, 
                items_claimed = items_claimed + ?,
                last_active = ?
            WHERE user_id = ?
        ''', (items_found_increment, items_claimed_increment, 
              datetime.now().isoformat(), user_id))
        conn.commit()
        return cursor.rowcount > 0

# Backward compatibility functions
def update_finder_stats(finder_id, items_found_increment=0, reputation_increment=0):
    """Update finder statistics (backward compatibility)."""
    return update_user_stats(finder_id, items_found_increment, 0)

def update_collector_stats(collector_id, items_claimed_increment=0, verification_status=None):
    """Update collector statistics (backward compatibility)."""
    return update_user_stats(collector_id, 0, items_claimed_increment)

# Get all functions for admin/reporting
def get_all_finders():
    """Get all finders in the system."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM FINDERS ORDER BY created_at DESC')
        return cursor.fetchall()

def get_all_collectors():
    """Get all collectors in the system."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM COLLECTORS ORDER BY created_at DESC')
        return cursor.fetchall()

def init_boxes_table():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create table if it doesn't exist first
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS BOXES (
                id TEXT PRIMARY KEY,
                status TEXT DEFAULT 'available',
                door_status TEXT DEFAULT 'closed',
                capacity INTEGER DEFAULT 1,
                current_load INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if door_status column exists (for migration from old schema)
        cursor.execute("PRAGMA table_info(BOXES)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'door_status' not in columns:
            # Add door_status column to existing table
            cursor.execute('ALTER TABLE BOXES ADD COLUMN door_status TEXT DEFAULT "closed"')
            print("Added door_status column to BOXES table")
        
        conn.commit()
    
from datetime import datetime

def add_box(location, status=True, door_status=False, load=0):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO BOXES (status, location, load, door_status, last_accessed)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            1 if status else 0,          # store as boolean (SQLite uses int 0/1)
            location,
            load,
            1 if door_status else 0,     # store as boolean
            datetime.now().isoformat()   # last_accessed
        ))
        conn.commit()
        return cursor.lastrowid  # return the new auto-incremented box_id


def delete_box(box_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM BOXES WHERE box_id = ?', (box_id,))
        conn.commit()
        return cursor.rowcount  # number of rows deleted

from datetime import datetime

def update_box(box_id, status=None, door_status=None, location=None, load=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        fields, values = [], []
        
        if status is not None:
            fields.append("status = ?")
            values.append(1 if status else 0)  # store as boolean
        if door_status is not None:
            fields.append("door_status = ?")
            values.append(1 if door_status else 0)
        if location is not None:
            fields.append("location = ?")
            values.append(location)
        if load is not None:
            fields.append("load = ?")
            values.append(load)

        # Always update last_accessed timestamp
        fields.append("last_accessed = ?")
        values.append(datetime.now().isoformat())

        values.append(box_id)  # for WHERE clause

        sql = f'''
            UPDATE BOXES
            SET {", ".join(fields)}
            WHERE box_id = ?
        '''
        cursor.execute(sql, tuple(values))
        conn.commit()
        return cursor.rowcount  # number of rows updated


def get_box_status(box_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM BOXES WHERE box_id = ?', (box_id,))
        return cursor.fetchone()

def update_box_status(box_id, status=None, current_load=None, door_status=None, capacity=None):
    """Update one or more attributes of a box.

    Parameters:
        box_id (str/int): Identifier of the box row to update.
        status (str): New status string (e.g., 'available', 'collect_request').
        current_load (int): Updated current item load.
        door_status (str): 'open' or 'closed'.
        capacity (int): Max capacity of the box.
    Returns:
        int: Number of rows updated (0 if box not found or nothing to update).
    """
    fields = []
    values = []
    if status is not None:
        fields.append('status = ?')
        values.append(status)
    if current_load is not None:
        fields.append('current_load = ?')
        values.append(current_load)
    if door_status is not None:
        fields.append('door_status = ?')
        values.append(door_status)
    if capacity is not None:
        fields.append('capacity = ?')
        values.append(capacity)

    # Always update last_updated if we are changing something
    if not fields:
        return 0
    fields.append('last_updated = CURRENT_TIMESTAMP')

    with get_db_connection() as conn:
        cursor = conn.cursor()
        sql = f"UPDATE BOXES SET {', '.join(fields)} WHERE id = ? OR box_id = ?"  # support either column name in case of schema variation
        values.extend([box_id, box_id])
        cursor.execute(sql, tuple(values))
        conn.commit()
        return cursor.rowcount


def get_all_boxes():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM BOXES ORDER BY box_id')
        return cursor.fetchall()

def add_case(box_id, receiver_id=None, receiver_image_url=None, item_id=None, 
             status="available", case_close_at=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO CASES (box_id, receiver_image_url, receiver_id, item_id, status, case_close_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            box_id,
            receiver_image_url,
            receiver_id,
            item_id,
            status,
            case_close_at,
            datetime.now().isoformat()  # created_at
        ))
        conn.commit()
        return cursor.lastrowid  # return the new auto-incremented found_id

def update_case(found_id, box_id=None, receiver_id=None, receiver_image_url=None, 
                item_id=None, status=None, case_close_at=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        fields, values = [], []

        if box_id is not None:
            fields.append("box_id = ?")
            values.append(box_id)
        if receiver_id is not None:
            fields.append("receiver_id = ?")
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

        # nothing to update
        if not fields:
            return 0  

        values.append(found_id)  # WHERE clause

        sql = f'''
            UPDATE Cases
            SET {", ".join(fields)}
            WHERE found_id = ?
        '''
        cursor.execute(sql, tuple(values))
        conn.commit()
        return cursor.rowcount  # number of rows updated
    
def delete_case(case_id):
	with get_db_connection() as conn:
		cursor = conn.cursor()
		cursor.execute('DELETE FROM CASES WHERE found_id = ?', (case_id,))
		conn.commit()
		return cursor.rowcount  # number of rows deleted

def get_case(case_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM CASES WHERE found_id = ?', (case_id,))
        return cursor.fetchone()
    
def get_all_case():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM CASES ORDER BY found_id')
        return cursor.fetchall()

# Database is initialized when needed - removed automatic initialization
