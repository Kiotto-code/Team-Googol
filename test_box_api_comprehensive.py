#!/usr/bin/env python3
"""
Comprehensive test suite for Box API endpoints in box.py

This script tests all the box management API endpoints:
1. POST /box/register - Register a new box
2. GET /box/<box_id>/status - Get box status
3. POST /box/<box_id>/status - Update box status
4. POST /box/<box_id>/door/open - Open box door
5. POST /box/<box_id>/door/close - Close box door
6. POST /box/<box_id>/request_collection - Request collection
7. POST /box/<box_id>/collection_complete - Mark collection complete
8. GET /boxes - Get all boxes
9. GET /box/<box_id>/items - Get box items
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
TEST_BOX_ID = "test_box_001"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(test_name):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}Testing: {test_name}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.RESET}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ️  {message}{Colors.RESET}")

def make_request(method, endpoint, data=None, expected_status=200):
    """Make HTTP request and return response with error handling."""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n{Colors.BOLD}Request:{Colors.RESET} {method} {endpoint}")
    if data:
        print(f"{Colors.BOLD}Data:{Colors.RESET} {json.dumps(data, indent=2)}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        print(f"{Colors.BOLD}Status Code:{Colors.RESET} {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"{Colors.BOLD}Response:{Colors.RESET} {json.dumps(response_data, indent=2)}")
        except:
            print(f"{Colors.BOLD}Response:{Colors.RESET} {response.text}")
            response_data = {"raw_response": response.text}
        
        # Check if response matches expected status
        if response.status_code == expected_status:
            print_success(f"Request successful (Status: {response.status_code})")
        else:
            print_error(f"Unexpected status code. Expected: {expected_status}, Got: {response.status_code}")
        
        return response.status_code, response_data
        
    except requests.exceptions.ConnectionError:
        print_error("Connection failed! Make sure Flask server is running on http://localhost:5000")
        return None, None
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return None, None

def test_server_connection():
    """Test if the Flask server is running."""
    print_test_header("Server Connection Test")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print_success("Flask server is running!")
        return True
    except requests.exceptions.ConnectionError:
        print_error("Flask server is not running!")
        print_info("Please start the server with: python backend/app.py")
        return False
    except Exception as e:
        print_error(f"Connection test failed: {str(e)}")
        return False

def test_box_register():
    """Test POST /box/register endpoint."""
    print_test_header("Box Registration")
    
    # Test 1: Valid box registration
    data = {
        "box_id": TEST_BOX_ID,
        "capacity": 1,
        "status": "available"
    }
    status, response = make_request("POST", "/box/register", data)
    
    if status == 200:
        print_success("Box registered successfully")
        return True
    elif status == 500 and "already exists" in str(response):
        print_info("Box already exists - this is expected in repeated tests")
        return True
    else:
        print_error("Box registration failed")
        return False

def test_box_register_errors():
    """Test error cases for box registration."""
    print_test_header("Box Registration Error Cases")
    
    # Test: Missing box_id
    print("\n--- Testing missing box_id ---")
    data = {"capacity": 1}
    make_request("POST", "/box/register", data, expected_status=400)
    
    # Test: Empty data
    print("\n--- Testing empty data ---")
    make_request("POST", "/box/register", {}, expected_status=400)
    
    # Test: No JSON data
    print("\n--- Testing no data ---")
    make_request("POST", "/box/register", None, expected_status=400)

def test_get_box_status():
    """Test GET /box/<box_id>/status endpoint."""
    print_test_header("Get Box Status")
    
    # Test: Get existing box status
    status, response = make_request("GET", f"/box/{TEST_BOX_ID}/status")
    
    if status == 200:
        print_success("Box status retrieved successfully")
        
        # Verify expected fields
        expected_fields = ["box_id", "status", "door_status", "capacity", "current_load", 
                          "last_updated", "is_full", "should_open", "door_open"]
        
        for field in expected_fields:
            if field in response:
                print_success(f"Field '{field}' present: {response[field]}")
            else:
                print_error(f"Missing field: {field}")
        
        return True
    else:
        print_error("Failed to get box status")
        return False

def test_get_box_status_errors():
    """Test error cases for getting box status."""
    print_test_header("Get Box Status Error Cases")
    
    # Test: Non-existent box
    print("\n--- Testing non-existent box ---")
    make_request("GET", "/box/nonexistent_box/status", expected_status=404)

def test_update_box_status():
    """Test POST /box/<box_id>/status endpoint."""
    print_test_header("Update Box Status")
    
    # Test 1: Update status only
    print("\n--- Testing status update ---")
    data = {"status": "full"}
    status, response = make_request("POST", f"/box/{TEST_BOX_ID}/status", data)
    
    # Test 2: Update door_status only
    print("\n--- Testing door status update ---")
    data = {"door_status": "open"}
    make_request("POST", f"/box/{TEST_BOX_ID}/status", data)
    
    # Test 3: Update current_load only
    print("\n--- Testing load update ---")
    data = {"current_load": 1}
    make_request("POST", f"/box/{TEST_BOX_ID}/status", data)
    
    # Test 4: Update multiple fields
    print("\n--- Testing multiple field update ---")
    data = {
        "status": "available",
        "door_status": "closed",
        "current_load": 0
    }
    make_request("POST", f"/box/{TEST_BOX_ID}/status", data)
    
    return status == 200

def test_update_box_status_errors():
    """Test error cases for updating box status."""
    print_test_header("Update Box Status Error Cases")
    
    # Test: No data provided
    print("\n--- Testing no data ---")
    make_request("POST", f"/box/{TEST_BOX_ID}/status", {}, expected_status=400)
    
    # Test: Invalid box ID
    print("\n--- Testing invalid box ID ---")
    data = {"status": "available"}
    make_request("POST", "/box/invalid_box/status", data, expected_status=404)

def test_door_operations():
    """Test door open and close endpoints."""
    print_test_header("Door Operations")
    
    # Test 1: Open door
    print("\n--- Testing door open ---")
    status_open, response_open = make_request("POST", f"/box/{TEST_BOX_ID}/door/open")
    
    if status_open == 200:
        print_success("Door opened successfully")
        
        # Verify door status
        status, response = make_request("GET", f"/box/{TEST_BOX_ID}/status")
        if response and response.get("door_status") == "open":
            print_success("Door status verified as 'open'")
        else:
            print_error("Door status not updated correctly")
    
    # Test 2: Close door
    print("\n--- Testing door close ---")
    status_close, response_close = make_request("POST", f"/box/{TEST_BOX_ID}/door/close")
    
    if status_close == 200:
        print_success("Door closed successfully")
        
        # Verify door status
        status, response = make_request("GET", f"/box/{TEST_BOX_ID}/status")
        if response and response.get("door_status") == "closed":
            print_success("Door status verified as 'closed'")
        else:
            print_error("Door status not updated correctly")
    
    return status_open == 200 and status_close == 200

def test_door_operations_errors():
    """Test error cases for door operations."""
    print_test_header("Door Operations Error Cases")
    
    # Test: Invalid box ID for open
    print("\n--- Testing door open with invalid box ---")
    make_request("POST", "/box/invalid_box/door/open", expected_status=404)
    
    # Test: Invalid box ID for close
    print("\n--- Testing door close with invalid box ---")
    make_request("POST", "/box/invalid_box/door/close", expected_status=404)

def test_collection_workflow():
    """Test the complete collection workflow."""
    print_test_header("Collection Workflow")
    
    # Step 1: Request collection
    print("\n--- Step 1: Request collection ---")
    status1, response1 = make_request("POST", f"/box/{TEST_BOX_ID}/request_collection")
    
    if status1 == 200:
        print_success("Collection requested successfully")
        
        # Verify status changed to collect_request and door opened
        status, response = make_request("GET", f"/box/{TEST_BOX_ID}/status")
        if response:
            if response.get("status") == "collect_request":
                print_success("Box status changed to 'collect_request'")
            else:
                print_error(f"Expected status 'collect_request', got '{response.get('status')}'")
            
            if response.get("door_status") == "open":
                print_success("Door opened for collection")
            else:
                print_error(f"Expected door_status 'open', got '{response.get('door_status')}'")
    
    # Step 2: Complete collection
    print("\n--- Step 2: Complete collection ---")
    status2, response2 = make_request("POST", f"/box/{TEST_BOX_ID}/collection_complete")
    
    if status2 == 200:
        print_success("Collection completed successfully")
        
        # Verify status reset to available, door closed, load reset
        status, response = make_request("GET", f"/box/{TEST_BOX_ID}/status")
        if response:
            expected_values = {
                "status": "available",
                "door_status": "closed", 
                "current_load": 0
            }
            
            for key, expected_value in expected_values.items():
                actual_value = response.get(key)
                if actual_value == expected_value:
                    print_success(f"'{key}' correctly reset to '{expected_value}'")
                else:
                    print_error(f"'{key}' not reset correctly. Expected: {expected_value}, Got: {actual_value}")
    
    return status1 == 200 and status2 == 200

def test_collection_workflow_errors():
    """Test error cases for collection workflow."""
    print_test_header("Collection Workflow Error Cases")
    
    # Test: Invalid box ID for request collection
    print("\n--- Testing request collection with invalid box ---")
    make_request("POST", "/box/invalid_box/request_collection", expected_status=404)
    
    # Test: Invalid box ID for collection complete
    print("\n--- Testing collection complete with invalid box ---")
    make_request("POST", "/box/invalid_box/collection_complete", expected_status=404)

def test_get_all_boxes():
    """Test GET /boxes endpoint."""
    print_test_header("Get All Boxes")
    
    status, response = make_request("GET", "/boxes")
    
    if status == 200:
        print_success("Retrieved all boxes successfully")
        
        if "boxes" in response and "total_boxes" in response:
            print_success(f"Found {response['total_boxes']} box(es)")
            
            # Check if our test box is in the list
            test_box_found = False
            for box in response.get("boxes", []):
                if box.get("box_id") == TEST_BOX_ID:
                    test_box_found = True
                    print_success(f"Test box '{TEST_BOX_ID}' found in box list")
                    
                    # Verify box data structure
                    expected_fields = ["box_id", "status", "door_status", "capacity", 
                                     "current_load", "last_updated", "is_full", 
                                     "should_open", "door_open"]
                    
                    for field in expected_fields:
                        if field in box:
                            print_success(f"Box field '{field}' present")
                        else:
                            print_error(f"Missing box field: {field}")
                    break
            
            if not test_box_found:
                print_error(f"Test box '{TEST_BOX_ID}' not found in box list")
        else:
            print_error("Response missing 'boxes' or 'total_boxes' field")
        
        return True
    else:
        print_error("Failed to get all boxes")
        return False

def test_get_box_items():
    """Test GET /box/<box_id>/items endpoint."""
    print_test_header("Get Box Items")
    
    status, response = make_request("GET", f"/box/{TEST_BOX_ID}/items")
    
    if status == 200:
        print_success("Retrieved box items successfully")
        
        expected_fields = ["box_id", "items", "item_count"]
        for field in expected_fields:
            if field in response:
                print_success(f"Field '{field}' present")
            else:
                print_error(f"Missing field: {field}")
        
        if response.get("box_id") == TEST_BOX_ID:
            print_success(f"Correct box_id returned: {TEST_BOX_ID}")
        else:
            print_error(f"Wrong box_id. Expected: {TEST_BOX_ID}, Got: {response.get('box_id')}")
        
        item_count = response.get("item_count", 0)
        print_info(f"Box contains {item_count} item(s)")
        
        return True
    else:
        print_error("Failed to get box items")
        return False

def test_get_box_items_errors():
    """Test error cases for getting box items."""
    print_test_header("Get Box Items Error Cases")
    
    # Note: This endpoint doesn't return 404 for non-existent boxes,
    # it returns an empty items list. Let's test this behavior.
    print("\n--- Testing non-existent box (should return empty list) ---")
    status, response = make_request("GET", "/box/nonexistent_box/items")
    
    if status == 200:
        if response.get("item_count") == 0:
            print_success("Non-existent box correctly returns empty items list")
        else:
            print_error("Non-existent box should return empty items list")

def run_all_tests():
    """Run all test suites."""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 80)
    print("FINDR BOX API COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"{Colors.RESET}")
    
    # Test server connection first
    if not test_server_connection():
        print_error("Cannot proceed with tests - server not available")
        return False
    
    test_results = []
    
    # Core functionality tests
    test_results.append(("Box Registration", test_box_register()))
    test_results.append(("Get Box Status", test_get_box_status()))
    test_results.append(("Update Box Status", test_update_box_status()))
    test_results.append(("Door Operations", test_door_operations()))
    test_results.append(("Collection Workflow", test_collection_workflow()))
    test_results.append(("Get All Boxes", test_get_all_boxes()))
    test_results.append(("Get Box Items", test_get_box_items()))
    
    # Error case tests
    test_box_register_errors()
    test_get_box_status_errors()
    test_update_box_status_errors()
    test_door_operations_errors()
    test_collection_workflow_errors()
    test_get_box_items_errors()
    
    # Print summary
    print_test_header("TEST SUMMARY")
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        if result:
            print_success(f"{test_name}: PASSED")
            passed_tests += 1
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Colors.BOLD}Results: {passed_tests}/{total_tests} tests passed{Colors.RESET}")
    
    if passed_tests == total_tests:
        print_success("🎉 ALL TESTS PASSED!")
        return True
    else:
        print_error("❌ SOME TESTS FAILED")
        return False

def cleanup_test_box():
    """Clean up test box after tests."""
    print_test_header("Cleanup")
    print_info(f"Test box '{TEST_BOX_ID}' left in system for manual inspection")
    print_info("You can manually delete it from the database if needed")

if __name__ == "__main__":
    try:
        success = run_all_tests()
        cleanup_test_box()
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Test suite crashed: {str(e)}")
        sys.exit(1)