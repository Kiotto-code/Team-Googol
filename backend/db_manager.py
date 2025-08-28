#!/usr/bin/env python3
"""
Database management CLI tool for the Lost & Found system.
"""

import argparse
import json
from datetime import datetime
from database import (
    get_all_items, get_available_items, claim_item, 
    release_expired_claims, delete_item, init_database, clear_all_items
)

def list_items(available_only=False):
    """List all items or only available items."""
    if available_only:
        items = get_available_items()
        print("Available Items:")
    else:
        items = get_all_items()
        print("All Items:")
    
    if not items:
        print("No items found.")
        return
    
    print("-" * 80)
    for item in items:
        print(f"ID: {item['id']}")
        print(f"Filename: {item['filename']}")
        print(f"Description: {item['description'] or 'N/A'}")
        print(f"Status: {item['status']}")
        print(f"Uploaded: {item['uploaded_at']}")
        
        if item['status'] == 'claimed':
            print(f"Claimed by: {item['claimed_by']}")
            print(f"Claimed at: {item['claimed_at']}")
            print(f"Expires at: {item['expires_at']}")
        
        print("-" * 80)

def claim_item_cli(item_id, claimed_by):
    """Claim an item via CLI."""
    success, message = claim_item(item_id, claimed_by)
    print(f"Claim result: {message}")
    return success

def release_expired_cli():
    """Release expired claims."""
    released_count = release_expired_claims()
    print(f"Released {released_count} expired claims.")

def delete_item_cli(filename):
    """Delete an item by filename."""
    deleted = delete_item(filename)
    if deleted:
        print(f"Successfully deleted item: {filename}")
    else:
        print(f"Item not found: {filename}")

def clear_all_items_cli():
    """Clear all items from the database."""
    response = input("Are you sure you want to delete ALL items? This cannot be undone. (y/N): ")
    if response.lower() in ['y', 'yes']:
        deleted_count = clear_all_items()
        print(f"Successfully deleted {deleted_count} items from the database.")
    else:
        print("Operation cancelled.")

def main():
    parser = argparse.ArgumentParser(description="Lost & Found Database Management Tool")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List items')
    list_parser.add_argument('--available', action='store_true', 
                           help='Show only available items')
    
    # Claim command
    claim_parser = subparsers.add_parser('claim', help='Claim an item')
    claim_parser.add_argument('item_id', type=int, help='ID of the item to claim')
    claim_parser.add_argument('claimed_by', help='User identifier')
    
    # Release command
    subparsers.add_parser('release-expired', help='Release expired claims')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an item')
    delete_parser.add_argument('filename', help='Filename of the item to delete')
    
    # Clear command
    subparsers.add_parser('clear', help='Clear all items from the database')
    
    # Init command
    subparsers.add_parser('init', help='Initialize database')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'list':
        list_items(available_only=args.available)
    elif args.command == 'claim':
        claim_item_cli(args.item_id, args.claimed_by)
    elif args.command == 'release-expired':
        release_expired_cli()
    elif args.command == 'delete':
        delete_item_cli(args.filename)
    elif args.command == 'clear':
        clear_all_items_cli()
    elif args.command == 'init':
        init_database()
        print("Database initialized.")

if __name__ == "__main__":
    main()
