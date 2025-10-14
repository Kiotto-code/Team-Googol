#!/usr/bin/env python3
"""
Quick test script for FINDR API endpoints
"""
import requests
import json
import time

# Base URL for the API
BASE_URL = "http://127.0.0.1:5000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Health Check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_stats():
    """Test system stats endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        print(f"Stats: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Stats test failed: {e}")
        return False

def test_user_creation():
    """Test user creation"""
    try:
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpass123",
            "phone_number": "1234567890"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
        print(f"User Creation: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code in [201, 400]  # 400 if user already exists
    except Exception as e:
        print(f"User creation test failed: {e}")
        return False

def test_items_list():
    """Test getting items list"""
    try:
        response = requests.get(f"{BASE_URL}/api/items")
        print(f"Items List: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Items list test failed: {e}")
        return False

def main():
    print("Testing FINDR API...")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    time.sleep(1)
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("System Stats", test_stats),
        ("User Creation", test_user_creation),
        ("Items List", test_items_list)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))
        print(f"Result: {'✅ PASS' if result else '❌ FAIL'}")
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()