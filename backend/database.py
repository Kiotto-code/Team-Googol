#!/usr/bin/env python3
"""
New database module for FINDR system with updated schema.

Schema:
- User: user_id, name, password, phone_number, email, student_id, rfid_tag, items_found, items_find, created_at
- Item: item_id, description, image_url, image_embedding, description_embedding, status, finder_user_id, finder_img_url, created_at
- Box: box_id, status, location, load, door_status, last_accessed
- Case: found_id, box_id, reciver_image_url, reciver_id, item_id, status, case_close_at, created_at
"""

import sqlite3
import json
import os
import hashlib
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging

# Database path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'findr_new.db')

def init_database():
    """Initialize the database with the new schema."""
    with sqlite3.connect(DATABASE_PATH, timeout=15.0) as conn:
        cursor = conn.cursor()
        
        # Enable better concurrency
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('PRAGMA busy_timeout=15000;')
        cursor.execute('PRAGMA foreign_keys=ON;')
        
        # Create User table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS User (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                phone_number INTEGER,
                email TEXT UNIQUE NOT NULL,
                student_id INTEGER UNIQUE,
                rfid_tag TEXT UNIQUE,
                items_found INTEGER DEFAULT 0,
                items_find INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create Item table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Item (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                image_url TEXT,
                image_embedding TEXT,
                description_embedding TEXT,
                status TEXT DEFAULT 'available',
                finder_user_id INTEGER,
                finder_img_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (finder_user_id) REFERENCES User(user_id)
            )
        ''')
        
        # Create Box table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Box (
                box_id INTEGER PRIMARY KEY AUTOINCREMENT,
                status BOOLEAN DEFAULT 1,
                location TEXT,
                load INTEGER DEFAULT 0,
                door_status BOOLEAN DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create Case table (using quotes because Case is a reserved keyword)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS "Case" (
                found_id INTEGER PRIMARY KEY AUTOINCREMENT,
                box_id INTEGER,
                reciver_image_url TEXT,
                reciver_id INTEGER,
                item_id INTEGER,
                status TEXT DEFAULT 'available',
                case_close_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (box_id) REFERENCES Box(box_id),
                FOREIGN KEY (reciver_id) REFERENCES User(user_id),
                FOREIGN KEY (item_id) REFERENCES Item(item_id)
            )
        ''')
        
        conn.commit()
        print("Database initialized with new schema")

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=15.0)
    try:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA busy_timeout=15000;')
        conn.execute('PRAGMA foreign_keys=ON;')
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.close()

def hash_password(password):
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Verify password against hash."""
    return hash_password(password) == hashed_password

# =============================================================================
# USER OPERATIONS
# =============================================================================

def create_user(name, email, password, phone_number=None, student_id=None, rfid_tag=None):
    """Create a new user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        
        cursor.execute('''
            INSERT INTO User (name, email, password, phone_number, student_id, rfid_tag)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, email, hashed_password, phone_number, student_id, rfid_tag))
        
        conn.commit()
        return cursor.lastrowid

def get_user_by_id(user_id):
    """Get user by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

def get_user_by_email(email):
    """Get user by email."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE email = ?', (email,))
        return cursor.fetchone()

def get_user_by_rfid(rfid_tag):
    """Get user by RFID tag."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE rfid_tag = ?', (rfid_tag,))
        return cursor.fetchone()

def get_user_by_student_id(student_id):
    """Get user by student ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE student_id = ?', (student_id,))
        return cursor.fetchone()

def update_user_stats(user_id, items_found_increment=0, items_find_increment=0):
    """Update user statistics."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE User 
            SET items_found = items_found + ?, 
                items_find = items_find + ?
            WHERE user_id = ?
        ''', (items_found_increment, items_find_increment, user_id))
        conn.commit()
        return cursor.rowcount > 0

def authenticate_user(email, password):
    """Authenticate user with email and password."""
    user = get_user_by_email(email)
    if user and verify_password(password, user['password']):
        return user
    return None

def get_all_users():
    """Get all users."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User ORDER BY created_at DESC')
        return cursor.fetchall()

# =============================================================================
# ITEM OPERATIONS
# =============================================================================

def create_item(description, finder_user_id=None, image_url=None, image_embedding=None, 
                description_embedding=None, finder_img_url=None, status='available'):
    """Create a new item."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Convert embeddings to JSON strings for storage
        img_emb_json = json.dumps(image_embedding) if image_embedding else None
        desc_emb_json = json.dumps(description_embedding) if description_embedding else None
        
        cursor.execute('''
            INSERT INTO Item (description, image_url, image_embedding, description_embedding, 
                            status, finder_user_id, finder_img_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (description, image_url, img_emb_json, desc_emb_json, status, finder_user_id, finder_img_url))
        
        conn.commit()
        
        # Update finder stats if provided
        if finder_user_id:
            update_user_stats(finder_user_id, items_found_increment=1)
        
        return cursor.lastrowid

def get_item_by_id(item_id):
    """Get item by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Item WHERE item_id = ?', (item_id,))
        return cursor.fetchone()

def get_items_by_status(status='available'):
    """Get items by status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Item WHERE status = ? ORDER BY created_at DESC', (status,))
        return cursor.fetchall()

def get_items_by_finder(finder_user_id):
    """Get items found by a specific user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Item WHERE finder_user_id = ? ORDER BY created_at DESC', (finder_user_id,))
        return cursor.fetchall()

def update_item_status(item_id, status):
    """Update item status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE Item SET status = ? WHERE item_id = ?', (status, item_id))
        conn.commit()
        return cursor.rowcount > 0

def get_all_items():
    """Get all items."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Item ORDER BY created_at DESC')
        return cursor.fetchall()

def search_items_by_text(query_text):
    """Search items by description text."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM Item 
            WHERE description LIKE ? AND status = 'available'
            ORDER BY created_at DESC
        ''', (f'%{query_text}%',))
        return cursor.fetchall()

# =============================================================================
# BOX OPERATIONS
# =============================================================================

def create_box(location, status=True, door_status=False, load=0):
    """Create a new box."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Box (status, location, load, door_status, last_accessed)
            VALUES (?, ?, ?, ?, ?)
        ''', (status, location, load, door_status, datetime.now().isoformat()))
        
        conn.commit()
        return cursor.lastrowid

def get_box_by_id(box_id):
    """Get box by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Box WHERE box_id = ?', (box_id,))
        return cursor.fetchone()

def update_box(box_id, status=None, location=None, load=None, door_status=None):
    """Update box details."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        fields = []
        values = []
        
        if status is not None:
            fields.append('status = ?')
            values.append(status)
        if location is not None:
            fields.append('location = ?')
            values.append(location)
        if load is not None:
            fields.append('load = ?')
            values.append(load)
        if door_status is not None:
            fields.append('door_status = ?')
            values.append(door_status)
        
        # Always update last_accessed
        fields.append('last_accessed = ?')
        values.append(datetime.now().isoformat())
        
        if fields:
            values.append(box_id)
            cursor.execute(f'UPDATE Box SET {", ".join(fields)} WHERE box_id = ?', values)
            conn.commit()
            return cursor.rowcount > 0
        return False

def get_all_boxes():
    """Get all boxes."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Box ORDER BY box_id')
        return cursor.fetchall()

def get_boxes_by_status(status=True):
    """Get boxes by status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Box WHERE status = ? ORDER BY box_id', (status,))
        return cursor.fetchall()

# =============================================================================
# CASE OPERATIONS
# =============================================================================

def create_case(box_id, reciver_id=None, item_id=None, reciver_image_url=None, 
                status='available', case_close_at=None):
    """Create a new case."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO "Case" (box_id, reciver_id, item_id, reciver_image_url, status, case_close_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (box_id, reciver_id, item_id, reciver_image_url, status, case_close_at))
        
        conn.commit()
        return cursor.lastrowid

def get_case_by_id(found_id):
    """Get case by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "Case" WHERE found_id = ?', (found_id,))
        return cursor.fetchone()

def get_cases_by_box(box_id):
    """Get cases by box ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "Case" WHERE box_id = ? ORDER BY created_at DESC', (box_id,))
        return cursor.fetchall()

def get_cases_by_status(status='available'):
    """Get cases by status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "Case" WHERE status = ? ORDER BY created_at DESC', (status,))
        return cursor.fetchall()

def update_case(found_id, box_id=None, reciver_id=None, item_id=None, 
                reciver_image_url=None, status=None, case_close_at=None):
    """Update case details."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        fields = []
        values = []
        
        if box_id is not None:
            fields.append('box_id = ?')
            values.append(box_id)
        if reciver_id is not None:
            fields.append('reciver_id = ?')
            values.append(reciver_id)
        if item_id is not None:
            fields.append('item_id = ?')
            values.append(item_id)
        if reciver_image_url is not None:
            fields.append('reciver_image_url = ?')
            values.append(reciver_image_url)
        if status is not None:
            fields.append('status = ?')
            values.append(status)
        if case_close_at is not None:
            fields.append('case_close_at = ?')
            values.append(case_close_at)
        
        if fields:
            values.append(found_id)
            cursor.execute(f'UPDATE "Case" SET {", ".join(fields)} WHERE found_id = ?', values)
            conn.commit()
            return cursor.rowcount > 0
        return False

def get_all_cases():
    """Get all cases."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "Case" ORDER BY created_at DESC')
        return cursor.fetchall()

def claim_case(found_id, reciver_id, reciver_image_url=None):
    """Claim a case (update receiver info and status)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if case is available
        case = get_case_by_id(found_id)
        if not case or case['status'] != 'available':
            return False, "Case not available"
        
        # Update case with receiver info
        cursor.execute('''
            UPDATE "Case" 
            SET reciver_id = ?, reciver_image_url = ?, status = 'claimed'
            WHERE found_id = ?
        ''', (reciver_id, reciver_image_url, found_id))
        
        conn.commit()
        
        # Update receiver stats
        update_user_stats(reciver_id, items_find_increment=1)
        
        return True, "Case claimed successfully"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_user_dashboard_data(user_id):
    """Get dashboard data for a user."""
    user = get_user_by_id(user_id)
    if not user:
        return None
    
    items_found = get_items_by_finder(user_id)
    
    # Get cases where user is receiver
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "Case" WHERE reciver_id = ? ORDER BY created_at DESC', (user_id,))
        cases_claimed = cursor.fetchall()
    
    return {
        'user': dict(user),
        'items_found': [dict(item) for item in items_found],
        'cases_claimed': [dict(case) for case in cases_claimed],
        'stats': {
            'total_items_found': len(items_found),
            'total_cases_claimed': len(cases_claimed),
            'items_found_count': user['items_found'],
            'items_find_count': user['items_find']
        }
    }

def get_system_stats():
    """Get system-wide statistics."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Count totals
        cursor.execute('SELECT COUNT(*) FROM User')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Item')
        total_items = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Box')
        total_boxes = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM "Case"')
        total_cases = cursor.fetchone()[0]
        
        # Count by status
        cursor.execute("SELECT COUNT(*) FROM Item WHERE status = 'available'")
        available_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM \"Case\" WHERE status = 'available'")
        available_cases = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Box WHERE status = 1')
        active_boxes = cursor.fetchone()[0]
        
        return {
            'total_users': total_users,
            'total_items': total_items,
            'total_boxes': total_boxes,
            'total_cases': total_cases,
            'available_items': available_items,
            'available_cases': available_cases,
            'active_boxes': active_boxes
        }

def clear_all_data():
    """Clear all data from database (for testing)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM "Case"')
        cursor.execute('DELETE FROM Item')
        cursor.execute('DELETE FROM Box')
        cursor.execute('DELETE FROM User')
        conn.commit()
        print("All data cleared")

if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
    print("Database setup complete!")