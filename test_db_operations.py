#!/usr/bin/env python3
"""
Test script for database operations.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from database_new import (
    # User operations
    create_user, get_user_by_id, get_user_by_email, authenticate_user,
    # Item operations  
    create_item, get_item_by_id, update_item_status,
    # Box operations
    create_box, get_box_by_id, update_box,
    # Case operations
    create_case, get_case_by_id, claim_case, update_case,
    # Utility functions
    get_system_stats, get_user_dashboard_data
)

def test_user_operations():
    """Test user CRUD operations."""
    print("🧪 Testing User Operations...")
    
    # Test user creation
    print("  Creating new user...")
    user_id = create_user(
        name="Test User DB",
        email="testdb@example.com", 
        password="test123",
        phone_number=5555555555,
        student_id=99998,
        rfid_tag="TEST_DB_RFID"
    )
    print(f"  ✅ User created with ID: {user_id}")
    
    # Test user retrieval
    print("  Retrieving user by ID...")
    user = get_user_by_id(user_id)
    if user:
        print(f"  ✅ User found: {user['name']} ({user['email']})")
    else:
        print("  ❌ User not found")
        return False
    
    # Test user retrieval by email
    print("  Retrieving user by email...")
    user_by_email = get_user_by_email("testdb@example.com")
    if user_by_email:
        print(f"  ✅ User found by email: {user_by_email['name']}")
    else:
        print("  ❌ User not found by email")
        return False
    
    # Test authentication
    print("  Testing authentication...")
    auth_user = authenticate_user("testdb@example.com", "test123")
    if auth_user:
        print(f"  ✅ Authentication successful: {auth_user['name']}")
    else:
        print("  ❌ Authentication failed")
        return False
    
    print("  ✅ All user operations passed!\n")
    return user_id

def test_item_operations(finder_user_id):
    """Test item CRUD operations."""
    print("🧪 Testing Item Operations...")
    
    # Test item creation
    print("  Creating new item...")
    item_id = create_item(
        description="Test DB Item - Red water bottle with university logo",
        finder_user_id=finder_user_id,
        image_url="/uploads/test_db_item.jpg",
        status="available"
    )
    print(f"  ✅ Item created with ID: {item_id}")
    
    # Test item retrieval
    print("  Retrieving item by ID...")
    item = get_item_by_id(item_id)
    if item:
        print(f"  ✅ Item found: {item['description'][:50]}...")
    else:
        print("  ❌ Item not found")
        return False
    
    # Test item status update
    print("  Updating item status...")
    success = update_item_status(item_id, "claimed")
    if success:
        print("  ✅ Item status updated successfully")
        
        # Verify the update
        updated_item = get_item_by_id(item_id)
        if updated_item['status'] == 'claimed':
            print("  ✅ Status update verified")
        else:
            print("  ❌ Status update not applied")
            return False
    else:
        print("  ❌ Item status update failed")
        return False
    
    print("  ✅ All item operations passed!\n")
    return item_id

def test_box_operations():
    """Test box CRUD operations."""
    print("🧪 Testing Box Operations...")
    
    # Test box creation
    print("  Creating new box...")
    box_id = create_box(
        location="Test DB Location - Computer Lab",
        status=True,
        load=0,
        door_status=False
    )
    print(f"  ✅ Box created with ID: {box_id}")
    
    # Test box retrieval
    print("  Retrieving box by ID...")
    box = get_box_by_id(box_id)
    if box:
        print(f"  ✅ Box found: {box['location']}")
    else:
        print("  ❌ Box not found")
        return False
    
    # Test box update
    print("  Updating box...")
    success = update_box(box_id, load=3, door_status=True)
    if success:
        print("  ✅ Box updated successfully")
        
        # Verify the update
        updated_box = get_box_by_id(box_id)
        if updated_box['load'] == 3 and updated_box['door_status'] == 1:
            print("  ✅ Box update verified")
        else:
            print("  ❌ Box update not applied correctly")
            return False
    else:
        print("  ❌ Box update failed")
        return False
    
    print("  ✅ All box operations passed!\n")
    return box_id

def test_case_operations(box_id, item_id, user_id):
    """Test case CRUD operations."""
    print("🧪 Testing Case Operations...")
    
    # Test case creation
    print("  Creating new case...")
    case_id = create_case(
        box_id=box_id,
        item_id=item_id,
        status="available"
    )
    print(f"  ✅ Case created with ID: {case_id}")
    
    # Test case retrieval
    print("  Retrieving case by ID...")
    case = get_case_by_id(case_id)
    if case:
        print(f"  ✅ Case found: Box {case['box_id']}, Item {case['item_id']}")
    else:
        print("  ❌ Case not found")
        return False
    
    # Test case claiming
    print("  Claiming case...")
    success, message = claim_case(case_id, user_id, "/uploads/claimer_db_test.jpg")
    if success:
        print(f"  ✅ Case claimed successfully: {message}")
        
        # Verify the claim
        claimed_case = get_case_by_id(case_id)
        if claimed_case['status'] == 'claimed' and claimed_case['reciver_id'] == user_id:
            print("  ✅ Case claim verified")
        else:
            print("  ❌ Case claim not applied correctly")
            return False
    else:
        print(f"  ❌ Case claim failed: {message}")
        return False
    
    print("  ✅ All case operations passed!\n")
    return case_id

def test_utility_functions(user_id):
    """Test utility functions."""
    print("🧪 Testing Utility Functions...")
    
    # Test system stats
    print("  Getting system statistics...")
    stats = get_system_stats()
    if stats:
        print(f"  ✅ System stats: {stats['total_users']} users, {stats['total_items']} items")
    else:
        print("  ❌ Failed to get system stats")
        return False
    
    # Test user dashboard
    print("  Getting user dashboard...")
    dashboard = get_user_dashboard_data(user_id)
    if dashboard:
        user_stats = dashboard['stats']
        print(f"  ✅ Dashboard: {user_stats['total_items_found']} items found, {user_stats['total_cases_claimed']} cases claimed")
    else:
        print("  ❌ Failed to get user dashboard")
        return False
    
    print("  ✅ All utility functions passed!\n")
    return True

def main():
    """Run all database tests."""
    print("🚀 Starting Database Operations Testing...")
    print("=" * 50)
    
    try:
        # Test user operations
        user_id = test_user_operations()
        if not user_id:
            print("❌ User operations failed")
            return False
        
        # Test item operations
        item_id = test_item_operations(user_id)
        if not item_id:
            print("❌ Item operations failed")
            return False
        
        # Test box operations
        box_id = test_box_operations()
        if not box_id:
            print("❌ Box operations failed")
            return False
        
        # Test case operations
        case_id = test_case_operations(box_id, item_id, user_id)
        if not case_id:
            print("❌ Case operations failed")
            return False
        
        # Test utility functions
        if not test_utility_functions(user_id):
            print("❌ Utility functions failed")
            return False
        
        print("🎉 ALL DATABASE OPERATIONS PASSED!")
        print("✅ The new database schema is working perfectly!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)