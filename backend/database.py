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
        cursor.execute('''
            SELECT * FROM FOUND_ITEMS 
            WHERE status = 'available' OR (status = 'claimed' AND datetime('now') > expires_at)
        ''')
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
        expires_at = claimed_at + timedelta(hours=1)
        
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
        
        cursor.execute('''
            UPDATE FOUND_ITEMS 
            SET status = 'available', claimed_at = NULL, claimed_by = NULL, expires_at = NULL
            WHERE status = 'claimed' AND datetime('now') > expires_at
        ''')
        
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
        cursor.execute('''
            SELECT * FROM FOUND_ITEMS 
            WHERE status = 'available' OR (status = 'claimed' AND datetime('now') > expires_at)
        ''')
        
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

# Initialize database when module is imported
init_database()
