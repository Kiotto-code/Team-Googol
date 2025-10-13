#!/usr/bin/env python3
"""
Database management script for FINDR system.
"""

import sys
import os
import argparse
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_new import (
    init_database, clear_all_data, get_system_stats,
    create_user, create_item, create_box, create_case,
    get_all_users, get_all_items, get_all_boxes, get_all_cases
)

def create_sample_data():
    """Create sample data for testing."""
    print("Creating sample data...")
    
    # Create sample users
    print("Creating sample users...")
    user1_id = create_user(
        name="John Doe",
        email="john.doe@example.com",
        password="password123",
        phone_number=1234567890,
        student_id=12345,
        rfid_tag="RFID001"
    )
    
    user2_id = create_user(
        name="Jane Smith",
        email="jane.smith@example.com", 
        password="password456",
        phone_number=9876543210,
        student_id=67890,
        rfid_tag="RFID002"
    )
    
    user3_id = create_user(
        name="Bob Wilson",
        email="bob.wilson@example.com",
        password="password789",
        student_id=11111
    )
    
    print(f"Created users: {user1_id}, {user2_id}, {user3_id}")
    
    # Create sample boxes
    print("Creating sample boxes...")
    box1_id = create_box("Library - Level 1", status=True, load=2)
    box2_id = create_box("Student Center", status=True, load=1) 
    box3_id = create_box("Engineering Building", status=False, load=0)
    
    print(f"Created boxes: {box1_id}, {box2_id}, {box3_id}")
    
    # Create sample items
    print("Creating sample items...")
    item1_id = create_item(
        description="Black iPhone 13 with blue case",
        finder_user_id=user1_id,
        image_url="/uploads/phone1.jpg",
        status="available"
    )
    
    item2_id = create_item(
        description="Red Nike backpack with laptop inside",
        finder_user_id=user2_id,
        image_url="/uploads/backpack1.jpg", 
        status="available"
    )
    
    item3_id = create_item(
        description="Silver MacBook Pro 13 inch",
        finder_user_id=user1_id,
        status="claimed"
    )
    
    print(f"Created items: {item1_id}, {item2_id}, {item3_id}")
    
    # Create sample cases
    print("Creating sample cases...")
    case1_id = create_case(
        box_id=box1_id,
        item_id=item1_id,
        status="available"
    )
    
    case2_id = create_case(
        box_id=box2_id,
        item_id=item2_id,
        status="available"
    )
    
    case3_id = create_case(
        box_id=box1_id,
        item_id=item3_id,
        reciver_id=user3_id,
        status="claimed",
        case_close_at=datetime.now().isoformat()
    )
    
    print(f"Created cases: {case1_id}, {case2_id}, {case3_id}")
    print("Sample data created successfully!")

def list_all_data():
    """List all data in the database."""
    print("=== DATABASE CONTENTS ===\n")
    
    # List users
    users = get_all_users()
    print(f"USERS ({len(users)}):")
    for user in users:
        print(f"  ID: {user['user_id']}, Name: {user['name']}, Email: {user['email']}, "
              f"Student ID: {user['student_id']}, Items Found: {user['items_found']}, "
              f"Items Claimed: {user['items_find']}")
    print()
    
    # List items
    items = get_all_items()
    print(f"ITEMS ({len(items)}):")
    for item in items:
        finder_info = f"Finder: {item['finder_user_id']}" if item['finder_user_id'] else "No finder"
        print(f"  ID: {item['item_id']}, Description: {item['description'][:50]}..., "
              f"Status: {item['status']}, {finder_info}")
    print()
    
    # List boxes
    boxes = get_all_boxes()
    print(f"BOXES ({len(boxes)}):")
    for box in boxes:
        status_str = "Active" if box['status'] else "Inactive"
        door_str = "Open" if box['door_status'] else "Closed"
        print(f"  ID: {box['box_id']}, Location: {box['location']}, "
              f"Status: {status_str}, Load: {box['load']}, Door: {door_str}")
    print()
    
    # List cases
    cases = get_all_cases()
    print(f"CASES ({len(cases)}):")
    for case in cases:
        receiver_info = f"Receiver: {case['reciver_id']}" if case['reciver_id'] else "No receiver"
        print(f"  ID: {case['found_id']}, Box: {case['box_id']}, Item: {case['item_id']}, "
              f"Status: {case['status']}, {receiver_info}")
    print()

def show_stats():
    """Show database statistics."""
    stats = get_system_stats()
    print("=== DATABASE STATISTICS ===")
    print(f"Total Users: {stats['total_users']}")
    print(f"Total Items: {stats['total_items']}")
    print(f"Total Boxes: {stats['total_boxes']}")
    print(f"Total Cases: {stats['total_cases']}")
    print(f"Available Items: {stats['available_items']}")
    print(f"Available Cases: {stats['available_cases']}")
    print(f"Active Boxes: {stats['active_boxes']}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='FINDR Database Manager')
    parser.add_argument('command', choices=['init', 'clear', 'list', 'stats', 'sample'],
                       help='Command to execute')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'init':
            print("Initializing database...")
            init_database()
            print("Database initialized successfully!")
            
        elif args.command == 'clear':
            confirm = input("Are you sure you want to clear all data? (yes/no): ")
            if confirm.lower() == 'yes':
                clear_all_data()
                print("All data cleared!")
            else:
                print("Operation cancelled.")
                
        elif args.command == 'list':
            list_all_data()
            
        elif args.command == 'stats':
            show_stats()
            
        elif args.command == 'sample':
            # Initialize database first if needed
            init_database()
            create_sample_data()
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()