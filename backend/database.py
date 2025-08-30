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
                claimed_by TEXT,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME
            )
        ''')
        
        init_boxes_table()
        
        # Create COLLECTED_ITEMS table for items collected by collection system
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS COLLECTED_ITEMS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                box_id TEXT,
                imgtaken_timestamp REAL,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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

def claim_item(item_id, claimed_by):
    """Claim an item for 1 hour."""
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
        ''', (claimed_at.isoformat(), claimed_by, expires_at.isoformat(), item_id))
        
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
def collect_found_item(filename, imgtaken_timestamp, box_id):
    """Collect a found item."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO COLLECTED_ITEMS (filename, imgtaken_timestamp, box_id)
            VALUES (?, ?, ?)
        ''', (filename, imgtaken_timestamp, box_id))
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

# BOX
def init_boxes_table():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if door_status column exists
        cursor.execute("PRAGMA table_info(BOXES)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'door_status' not in columns:
            # Add door_status column to existing table
            cursor.execute('ALTER TABLE BOXES ADD COLUMN door_status TEXT DEFAULT "closed"')
            print("Added door_status column to BOXES table")
        
        # Create table if it doesn't exist
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



# Initialize database when module is imported
init_database()
