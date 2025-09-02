#!/usr/bin/env python3
"""
Test runner for the Lost & Found system.

This script runs all available tests in the tests/ directory.
"""

import os
import sys
import subprocess

def run_test(test_file):
    """Run a single test file and return the result."""
    print(f"\n{'='*50}")
    print(f"Running: {test_file}")
    print('='*50)
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=False, 
                              check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {test_file}: {e}")
        return False

def main():
    """Main test runner."""
    tests_dir = os.path.join(os.path.dirname(__file__))
    
    # Find all test files
    test_files = []
    for file in os.listdir(tests_dir):
        if file.startswith('test_') and file.endswith('.py'):
            test_files.append(os.path.join(tests_dir, file))
    
    if not test_files:
        print("No test files found!")
        return False
    
    print("Lost & Found System - Test Runner")
    print(f"Found {len(test_files)} test file(s)")
    
    # Run all tests
    results = []
    for test_file in test_files:
        success = run_test(test_file)
        results.append((test_file, success))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_file, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {os.path.basename(test_file)}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
