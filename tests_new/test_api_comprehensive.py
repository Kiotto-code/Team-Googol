#!/usr/bin/env python3
"""
Comprehensive test suite for the new FINDR API system.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:5000"
API_URL = f"{BASE_URL}/api"

class APITester:
    """API testing class for FINDR system."""
    
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        
    def log(self, message, level="INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_health_check(self):
        """Test health check endpoint."""
        self.log("Testing health check...")
        
        try:
            response = self.session.get(f"{API_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Health check passed: {data['status']}")
                return True
            else:
                self.log(f"❌ Health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Health check error: {e}", "ERROR")
            return False
    
    def test_auth_endpoints(self):
        """Test authentication endpoints."""
        self.log("Testing authentication endpoints...")
        
        # Test user registration
        self.log("Testing user registration...")
        register_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpass123",
            "phone_number": 1234567890,
            "student_id": 99999,
            "rfid_tag": "TEST_RFID_001"
        }
        
        try:
            response = self.session.post(f"{API_URL}/auth/register", json=register_data)
            
            if response.status_code == 201:
                data = response.json()
                self.test_data['user_id'] = data['user_id']
                self.log(f"✅ User registration successful: User ID {data['user_id']}")
            else:
                self.log(f"❌ User registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ User registration error: {e}", "ERROR")
            return False
        
        # Test user login
        self.log("Testing user login...")
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        try:
            response = self.session.post(f"{API_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ User login successful: {data['user']['name']}")
            else:
                self.log(f"❌ User login failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ User login error: {e}", "ERROR")
            return False
        
        # Test session check
        self.log("Testing session check...")
        try:
            response = self.session.get(f"{API_URL}/auth/session")
            
            if response.status_code == 200:
                data = response.json()
                if data['authenticated']:
                    self.log(f"✅ Session check successful: Authenticated as {data['email']}")
                else:
                    self.log("❌ Session check failed: Not authenticated", "ERROR")
                    return False
            else:
                self.log(f"❌ Session check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Session check error: {e}", "ERROR")
            return False
        
        return True
    
    def test_user_endpoints(self):
        """Test user management endpoints."""
        self.log("Testing user endpoints...")
        
        # Test get all users
        self.log("Testing get all users...")
        try:
            response = self.session.get(f"{API_URL}/users/")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Get all users successful: {data['count']} users found")
            else:
                self.log(f"❌ Get all users failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Get all users error: {e}", "ERROR")
            return False
        
        # Test get user by ID
        if 'user_id' in self.test_data:
            self.log(f"Testing get user by ID: {self.test_data['user_id']}...")
            try:
                response = self.session.get(f"{API_URL}/users/{self.test_data['user_id']}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"✅ Get user by ID successful: {data['data']['name']}")
                else:
                    self.log(f"❌ Get user by ID failed: {response.status_code}", "ERROR")
                    return False
            except Exception as e:
                self.log(f"❌ Get user by ID error: {e}", "ERROR")
                return False
        
        # Test user dashboard
        if 'user_id' in self.test_data:
            self.log(f"Testing user dashboard: {self.test_data['user_id']}...")
            try:
                response = self.session.get(f"{API_URL}/users/{self.test_data['user_id']}/dashboard")
                
                if response.status_code == 200:
                    data = response.json()
                    stats = data['data']['stats']
                    self.log(f"✅ User dashboard successful: {stats['total_items_found']} items found, {stats['total_cases_claimed']} cases claimed")
                else:
                    self.log(f"❌ User dashboard failed: {response.status_code}", "ERROR")
                    return False
            except Exception as e:
                self.log(f"❌ User dashboard error: {e}", "ERROR")
                return False
        
        return True
    
    def test_box_endpoints(self):
        """Test box management endpoints."""
        self.log("Testing box endpoints...")
        
        # Test create box
        self.log("Testing create box...")
        box_data = {
            "location": "Test Location - API Testing",
            "status": True,
            "load": 0,
            "door_status": False
        }
        
        try:
            response = self.session.post(f"{API_URL}/boxes/", json=box_data)
            
            if response.status_code == 201:
                data = response.json()
                self.test_data['box_id'] = data['box_id']
                self.log(f"✅ Box creation successful: Box ID {data['box_id']}")
            else:
                self.log(f"❌ Box creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Box creation error: {e}", "ERROR")
            return False
        
        # Test get all boxes
        self.log("Testing get all boxes...")
        try:
            response = self.session.get(f"{API_URL}/boxes/")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Get all boxes successful: {data['count']} boxes found")
            else:
                self.log(f"❌ Get all boxes failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Get all boxes error: {e}", "ERROR")
            return False
        
        # Test update box
        if 'box_id' in self.test_data:
            self.log(f"Testing update box: {self.test_data['box_id']}...")
            update_data = {
                "load": 5,
                "door_status": True
            }
            
            try:
                response = self.session.put(f"{API_URL}/boxes/{self.test_data['box_id']}", json=update_data)
                
                if response.status_code == 200:
                    self.log("✅ Box update successful")
                else:
                    self.log(f"❌ Box update failed: {response.status_code}", "ERROR")
                    return False
            except Exception as e:
                self.log(f"❌ Box update error: {e}", "ERROR")
                return False
        
        return True
    
    def test_item_endpoints(self):
        """Test item management endpoints."""
        self.log("Testing item endpoints...")
        
        # Test create item
        self.log("Testing create item...")
        item_data = {
            "description": "Test item for API testing - Blue water bottle with stickers",
            "finder_user_id": self.test_data.get('user_id'),
            "image_url": "/uploads/test_item.jpg",
            "status": "available"
        }
        
        try:
            response = self.session.post(f"{API_URL}/items/", json=item_data)
            
            if response.status_code == 201:
                data = response.json()
                self.test_data['item_id'] = data['item_id']
                self.log(f"✅ Item creation successful: Item ID {data['item_id']}")
            else:
                self.log(f"❌ Item creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Item creation error: {e}", "ERROR")
            return False
        
        # Test get all items
        self.log("Testing get all items...")
        try:
            response = self.session.get(f"{API_URL}/items/")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Get all items successful: {data['count']} items found")
            else:
                self.log(f"❌ Get all items failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Get all items error: {e}", "ERROR")
            return False
        
        # Test get available items
        self.log("Testing get available items...")
        try:
            response = self.session.get(f"{API_URL}/items/available")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Get available items successful: {data['count']} available items")
            else:
                self.log(f"❌ Get available items failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Get available items error: {e}", "ERROR")
            return False
        
        return True
    
    def test_case_endpoints(self):
        """Test case management endpoints."""
        self.log("Testing case endpoints...")
        
        # Test create case
        if 'box_id' in self.test_data and 'item_id' in self.test_data:
            self.log("Testing create case...")
            case_data = {
                "box_id": self.test_data['box_id'],
                "item_id": self.test_data['item_id'],
                "status": "available"
            }
            
            try:
                response = self.session.post(f"{API_URL}/cases/", json=case_data)
                
                if response.status_code == 201:
                    data = response.json()
                    self.test_data['case_id'] = data['found_id']
                    self.log(f"✅ Case creation successful: Case ID {data['found_id']}")
                else:
                    self.log(f"❌ Case creation failed: {response.status_code} - {response.text}", "ERROR")
                    return False
            except Exception as e:
                self.log(f"❌ Case creation error: {e}", "ERROR")
                return False
        
        # Test get all cases
        self.log("Testing get all cases...")
        try:
            response = self.session.get(f"{API_URL}/cases/")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Get all cases successful: {data['count']} cases found")
            else:
                self.log(f"❌ Get all cases failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Get all cases error: {e}", "ERROR")
            return False
        
        # Test claim case
        if 'case_id' in self.test_data and 'user_id' in self.test_data:
            self.log(f"Testing claim case: {self.test_data['case_id']}...")
            claim_data = {
                "reciver_id": self.test_data['user_id'],
                "reciver_image_url": "/uploads/claimer_photo.jpg"
            }
            
            try:
                response = self.session.post(f"{API_URL}/cases/{self.test_data['case_id']}/claim", json=claim_data)
                
                if response.status_code == 200:
                    self.log("✅ Case claim successful")
                else:
                    self.log(f"❌ Case claim failed: {response.status_code} - {response.text}", "ERROR")
                    return False
            except Exception as e:
                self.log(f"❌ Case claim error: {e}", "ERROR")
                return False
        
        return True
    
    def test_search_endpoints(self):
        """Test search endpoints."""
        self.log("Testing search endpoints...")
        
        # Test search items
        self.log("Testing search items...")
        try:
            response = self.session.get(f"{API_URL}/search/items?q=water")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Search items successful: {data['count']} items found for 'water'")
            else:
                self.log(f"❌ Search items failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Search items error: {e}", "ERROR")
            return False
        
        # Test search suggestions
        self.log("Testing search suggestions...")
        try:
            response = self.session.get(f"{API_URL}/search/suggestions?q=te")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Search suggestions successful: {data['count']} suggestions for 'te'")
            else:
                self.log(f"❌ Search suggestions failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Search suggestions error: {e}", "ERROR")
            return False
        
        return True
    
    def test_stats_endpoints(self):
        """Test statistics endpoints."""
        self.log("Testing statistics endpoints...")
        
        # Test system stats
        self.log("Testing system stats...")
        try:
            response = self.session.get(f"{API_URL}/stats")
            
            if response.status_code == 200:
                data = response.json()
                stats = data['data']
                self.log(f"✅ System stats successful: {stats['total_users']} users, {stats['total_items']} items, {stats['total_boxes']} boxes, {stats['total_cases']} cases")
            else:
                self.log(f"❌ System stats failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ System stats error: {e}", "ERROR")
            return False
        
        # Test user stats
        self.log("Testing user stats...")
        try:
            response = self.session.get(f"{API_URL}/users/stats")
            
            if response.status_code == 200:
                data = response.json()
                stats = data['data']
                self.log(f"✅ User stats successful: {stats['total_users']} users, {stats['total_items_found']} items found")
            else:
                self.log(f"❌ User stats failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ User stats error: {e}", "ERROR")
            return False
        
        return True
    
    def run_all_tests(self):
        """Run all API tests."""
        self.log("🚀 Starting comprehensive API testing...")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Authentication", self.test_auth_endpoints),
            ("User Management", self.test_user_endpoints),
            ("Box Management", self.test_box_endpoints),
            ("Item Management", self.test_item_endpoints),
            ("Case Management", self.test_case_endpoints),
            ("Search Functions", self.test_search_endpoints),
            ("Statistics", self.test_stats_endpoints)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n{'='*50}")
            self.log(f"Running {test_name} tests...")
            self.log(f"{'='*50}")
            
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name} tests PASSED")
                else:
                    failed += 1
                    self.log(f"❌ {test_name} tests FAILED", "ERROR")
            except Exception as e:
                failed += 1
                self.log(f"❌ {test_name} tests FAILED with exception: {e}", "ERROR")
        
        # Final results
        self.log(f"\n{'='*50}")
        self.log("🏁 FINAL TEST RESULTS")
        self.log(f"{'='*50}")
        self.log(f"✅ Tests Passed: {passed}")
        self.log(f"❌ Tests Failed: {failed}")
        self.log(f"📊 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            self.log("🎉 ALL TESTS PASSED! API is working perfectly.")
            return True
        else:
            self.log(f"⚠️  {failed} test suite(s) failed. Please check the errors above.", "WARNING")
            return False

def main():
    """Main function."""
    print("FINDR API Test Suite")
    print("===================")
    
    tester = APITester()
    
    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Server is running at {BASE_URL}")
    except requests.exceptions.RequestException:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("Please make sure the FINDR server is running:")
        print("  python backend/app_new.py")
        sys.exit(1)
    
    # Run all tests
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()