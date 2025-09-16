import sqlite3
import json
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging

DATABASE_PATH = 'lost_and_found.db'

def init_database():
    """Initialize the database with the required tables."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Initialize user tables first (FINDERS and COLLECTORS)
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
                claimed_by INTEGER,  -- References COLLECTORS.collector_id
                finder_id INTEGER,   -- References FINDERS.finder_id 
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                FOREIGN KEY (claimed_by) REFERENCES COLLECTORS (collector_id),
                FOREIGN KEY (finder_id) REFERENCES FINDERS (finder_id)
            )
        ''')
        
        # Create COLLECTED_ITEMS table for items collected by collection system
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS COLLECTED_ITEMS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                box_id TEXT,
                finder_id INTEGER,  -- References FINDERS.finder_id (system or person who found it)
                imgtaken_timestamp REAL,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (finder_id) REFERENCES FINDERS (finder_id)
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
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    try:
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
        
        # Update collector's last active timestamp and stats
        update_collector_stats(claimed_by_collector_id, items_claimed_increment=1)
        
        conn.commit()
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
        
        import numpy as np
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
            final_score = (img_score + desc_score) / 2 if desc_score != 0 else img_score
            
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
            update_finder_stats(finder_id, items_found_increment=1, reputation_increment=1)
            
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

# USER MANAGEMENT - Separated into FINDERS and COLLECTORS tables
def init_finders_table():
    """Initialize the FINDERS table for people who find and report items."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS FINDERS (
                finder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                rfid_tag TEXT UNIQUE,
                items_found INTEGER DEFAULT 0,  -- Count of items they've found
                reputation_score INTEGER DEFAULT 0,  -- Based on successful matches
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def init_collectors_table():
    """Initialize the COLLECTORS table for people who lost items and want to claim them."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS COLLECTORS (
                collector_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                student_id TEXT UNIQUE,  -- For university students
                id_number TEXT,  -- National ID or other identification
                items_claimed INTEGER DEFAULT 0,  -- Count of items they've claimed
                verification_status TEXT DEFAULT 'unverified',  -- 'verified', 'unverified', 'pending'
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def init_users_table():
    """Initialize both FINDERS and COLLECTORS tables."""
    init_finders_table()
    init_collectors_table()
    
    # Migrate existing USERS table if it exists
    migrate_users_to_separated_tables()

def migrate_users_to_separated_tables():
    """Migrate existing USERS table data to FINDERS and COLLECTORS tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if old USERS table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='USERS'")
        if cursor.fetchone():
            print("Migrating existing USERS table to FINDERS and COLLECTORS...")
            
            # Get all existing users
            cursor.execute('SELECT * FROM USERS')
            existing_users = cursor.fetchall()
            
            for user in existing_users:
                user_dict = dict(user)
                user_type = user_dict.get('user_type', 'both')
                
                # Add to FINDERS if they are finder or both
                if user_type in ['finder', 'both']:
                    cursor.execute('''
                        INSERT OR IGNORE INTO FINDERS (name, email, rfid_tag, created_at, last_active)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_dict['name'], user_dict['email'], user_dict['rfid_tag'],
                          user_dict['created_at'], user_dict['last_active']))
                
                # Add to COLLECTORS if they are collector or both
                if user_type in ['collector', 'both']:
                    cursor.execute('''
                        INSERT OR IGNORE INTO COLLECTORS (name, email, created_at, last_active)
                        VALUES (?, ?, ?, ?)
                    ''', (user_dict['name'], user_dict['email'],
                          user_dict['created_at'], user_dict['last_active']))
            
            # Rename old table for backup
            cursor.execute('ALTER TABLE USERS RENAME TO USERS_BACKUP')
            print("Migration completed. Old USERS table renamed to USERS_BACKUP")
            
        conn.commit()

# FINDER management functions
def add_finder(name, email=None, phone=None, rfid_tag=None):
    """Add a new finder to the system."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO FINDERS (name, email, phone, rfid_tag, created_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, rfid_tag, 
              datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid

def get_finder_by_id(finder_id):
    """Get finder information by finder ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM FINDERS WHERE finder_id = ?', (finder_id,))
        return cursor.fetchone()

def get_finder_by_email(email):
    """Get finder information by email."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM FINDERS WHERE email = ?', (email,))
        return cursor.fetchone()

def get_finder_by_rfid(rfid_tag):
    """Get finder information by RFID tag."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM FINDERS WHERE rfid_tag = ?', (rfid_tag,))
        return cursor.fetchone()

def update_finder_stats(finder_id, items_found_increment=0, reputation_increment=0):
    """Update finder statistics."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE FINDERS 
            SET items_found = items_found + ?, 
                reputation_score = reputation_score + ?,
                last_active = ?
            WHERE finder_id = ?
        ''', (items_found_increment, reputation_increment, 
              datetime.now().isoformat(), finder_id))
        conn.commit()
        return cursor.rowcount > 0

# COLLECTOR management functions  
def add_collector(name, email=None, phone=None, student_id=None, id_number=None):
    """Add a new collector (item claimer) to the system."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO COLLECTORS (name, email, phone, student_id, id_number, created_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, student_id, id_number,
              datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid

def get_collector_by_id(collector_id):
    """Get collector information by collector ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM COLLECTORS WHERE collector_id = ?', (collector_id,))
        return cursor.fetchone()

def get_collector_by_email(email):
    """Get collector information by email.""" 
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM COLLECTORS WHERE email = ?', (email,))
        return cursor.fetchone()

def get_collector_by_student_id(student_id):
    """Get collector information by student ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM COLLECTORS WHERE student_id = ?', (student_id,))
        return cursor.fetchone()

def update_collector_stats(collector_id, items_claimed_increment=0, verification_status=None):
    """Update collector statistics and verification status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if verification_status:
            cursor.execute('''
                UPDATE COLLECTORS 
                SET items_claimed = items_claimed + ?, 
                    verification_status = ?,
                    last_active = ?
                WHERE collector_id = ?
            ''', (items_claimed_increment, verification_status,
                  datetime.now().isoformat(), collector_id))
        else:
            cursor.execute('''
                UPDATE COLLECTORS 
                SET items_claimed = items_claimed + ?, 
                    last_active = ?
                WHERE collector_id = ?
            ''', (items_claimed_increment, datetime.now().isoformat(), collector_id))
        conn.commit()
        return cursor.rowcount > 0

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

def add_box(box_id, capacity=1, status="available", door_status="closed"):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO BOXES (id, capacity, status, door_status, current_load, last_updated)
            VALUES (?, ?, ?, ?, 0, ?)
        ''', (box_id, capacity, status, door_status, datetime.now().isoformat()))
        conn.commit()
        return box_id
    
def delete_box(box_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM BOXES WHERE id = ?', (box_id,))
        conn.commit()
        return cursor.rowcount  # number of rows deleted

def update_box_status(box_id, status=None, door_status=None, current_load=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        fields, values = [], []
        
        if status is not None:
            fields.append("status = ?")
            values.append(status)
        if door_status is not None:
            fields.append("door_status = ?")
            values.append(door_status)
        if current_load is not None:
            fields.append("current_load = ?")
            values.append(current_load)
        
        values.append(datetime.now().isoformat())  # last_updated
        values.append(box_id)
        
        cursor.execute(f'''
            UPDATE BOXES 
            SET {", ".join(fields)}, last_updated = ?
            WHERE id = ?
        ''', tuple(values))
        conn.commit()
        return cursor.rowcount > 0


def get_box_status(box_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM BOXES WHERE id = ?', (box_id,))
        return cursor.fetchone()


def get_all_boxes():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM BOXES ORDER BY id')
        return cursor.fetchall()



# Database is initialized when needed - removed automatic initialization
