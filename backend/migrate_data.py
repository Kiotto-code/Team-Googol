#!/usr/bin/env python3
"""
Migration script to convert data.json to SQLite database.
Run this script once to migrate existing data.
"""

import os
import json
import sys
from database import add_found_item, init_database

def migrate_json_to_sqlite():
    """Migrate data from data.json to SQLite database."""
    
    # Initialize database
    init_database()
    
    data_file = "data.json"
    
    if not os.path.exists(data_file):
        print("No data.json file found. Nothing to migrate.")
        return
    
    try:
        with open(data_file, 'r') as f:
            image_data = json.load(f)
    except Exception as e:
        print(f"Error reading data.json: {e}")
        return
    
    if not image_data:
        print("data.json is empty. Nothing to migrate.")
        return
    
    migrated_count = 0
    error_count = 0
    
    for filename, item in image_data.items():
        try:
            # Extract data from JSON format
            image_embedding = item.get("image_embedding", [])
            description_embedding = item.get("description_embedding")
            description = item.get("description", "")
            
            # Add to database
            item_id = add_found_item(
                filename=filename,
                image_embedding=image_embedding,
                description=description,
                description_embedding=description_embedding
            )
            
            print(f"Migrated: {filename} -> ID: {item_id}")
            migrated_count += 1
            
        except Exception as e:
            print(f"Error migrating {filename}: {e}")
            error_count += 1
    
    print(f"\nMigration completed:")
    print(f"  Successfully migrated: {migrated_count} items")
    print(f"  Errors: {error_count} items")
    
    if migrated_count > 0:
        # Backup the original file
        backup_file = f"{data_file}.backup"
        os.rename(data_file, backup_file)
        print(f"  Original data.json backed up to {backup_file}")

if __name__ == "__main__":
    migrate_json_to_sqlite()
