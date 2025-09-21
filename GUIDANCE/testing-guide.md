# Testing Guide - FINDR System

This guide covers testing procedures, test interpretation, and quality assurance for the FINDR Smart Lost & Found system.

## 🧪 Testing Overview

The FINDR system includes comprehensive testing to ensure reliability:

- **Unit Tests**: Individual component functionality
- **Integration Tests**: API endpoint testing
- **Database Tests**: Data integrity and operations
- **System Tests**: End-to-end workflow validation
- **Performance Tests**: Response time and load testing

## 🚀 Quick Test Execution

### Run All Tests

```bash
# Navigate to project root
cd /home/chan/work/ticket

# Run complete test suite
python tests/run_tests.py
```

**Expected Output:**
```
Lost & Found System - Test Runner
Found 3 test file(s)

==================================================
Running: /home/chan/work/ticket/tests/test_collect.py
==================================================
Testing collect database functionality...
✓ Database initialized
✓ Item collected successfully with ID: 1
✓ Collection data retrieved successfully
...

==================================================
TEST SUMMARY
==================================================
✅ test_collect.py: PASSED
✅ test_box_api.py: PASSED  
✅ test_api_endpoints.py: PASSED

Tests: 3 passed, 0 failed
Overall: ✅ ALL TESTS PASSED
```

### Run Individual Tests

```bash
# Test collection functionality
python tests/test_collect.py

# Test box API functionality
python tests/test_box_api.py

# Test specific components
python tests/test_specific_feature.py
```

## 📋 Test Categories

### 1. Collection Tests (`test_collect.py`)

**What it tests:**
- Database operations for collected items
- File system operations for collector folder
- Integration with collect endpoint
- Timestamp and metadata handling

**Key Test Cases:**
```python
def test_collect_database():
    """Test database collection functionality"""
    # Tests item collection storage
    # Verifies data retrieval
    # Checks timestamp handling

def test_collect_file_operations():
    """Test file operations during collection"""
    # Tests file copying to collectors folder
    # Verifies file permissions and paths
    # Checks error handling for missing files
```

**Running Collection Tests:**
```bash
python tests/test_collect.py
```

**Expected Results:**
- ✓ Database initialized
- ✓ Item collected successfully
- ✓ Collection data retrieved
- ✓ File copied to collectors folder
- ✓ Original file preserved

### 2. Box API Tests (`test_box_api.py`)

**What it tests:**
- Box registration and management
- Status updates and validation
- Door control mechanisms
- Error handling and edge cases

**Key Test Cases:**
```python
def test_box_registration():
    """Test box registration API"""
    # Tests new box creation
    # Validates input parameters
    # Checks duplicate handling

def test_box_status_updates():
    """Test box status management"""
    # Tests status transitions
    # Validates status combinations
    # Checks business logic enforcement

def test_door_operations():
    """Test door control"""
    # Tests door open/close commands
    # Validates security rules
    # Checks error conditions
```

### 3. Database Tests

**What it tests:**
- Schema validation
- Data integrity constraints
- Migration procedures
- Performance under load

**Running Database Tests:**
```bash
# Test database initialization
python backend/db_manager.py --test

# Test specific database operations
python tests/test_database_operations.py
```

## 🔍 API Testing

### Manual API Testing

**Test Item Upload:**
```bash
# Test image upload with validation
curl -X POST http://localhost:5000/upload \
  -F "image=@tests/test_images/sample_item.jpg" \
  -F "description=Test item for upload validation" \
  -F "finder_id=1"

# Expected: 200 OK with item details
```

**Test Item Search:**
```bash
# Test search functionality
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test item blue water bottle"}'

# Expected: Results array with similarity scores
```

**Test Box Operations:**
```bash
# Test box status retrieval
curl http://localhost:5000/box/test_box/status

# Test box door control
curl -X POST http://localhost:5000/box/test_box/door/open

# Expected: Status confirmation and door state update
```

### Automated API Testing

**Using Python requests:**
```python
import requests
import json

def test_upload_endpoint():
    """Test upload API endpoint"""
    url = "http://localhost:5000/upload"
    files = {'image': open('test_image.jpg', 'rb')}
    data = {'description': 'Test upload', 'finder_id': 1}
    
    response = requests.post(url, files=files, data=data)
    assert response.status_code == 200
    
    result = response.json()
    assert 'filename' in result
    assert 'message' in result
    print("✓ Upload endpoint test passed")

def test_search_endpoint():
    """Test search API endpoint"""
    url = "http://localhost:5000/search"
    data = {'query': 'blue water bottle'}
    
    response = requests.post(url, json=data)
    assert response.status_code in [200, 400]  # 400 if no results
    
    if response.status_code == 200:
        result = response.json()
        assert 'results' in result
    print("✓ Search endpoint test passed")
```

## 📊 Test Data Management

### Test Database Setup

**Initialize Test Environment:**
```bash
# Create test database
export TEST_DB_PATH="/tmp/test_findr.db"
python backend/db_manager.py --init --database $TEST_DB_PATH

# Populate test data
python tests/setup_test_data.py
```

**Test Data Structure:**
```
tests/
├── test_images/           # Sample images for testing
│   ├── sample_item.jpg
│   ├── test_upload.png
│   └── validation_test.webp
├── test_data/            # Test database and files
│   ├── test_items.json
│   └── sample_users.json
└── fixtures/             # Reusable test fixtures
```

### Sample Test Data

**Test Users:**
```json
{
  "finders": [
    {
      "name": "Test Finder",
      "email": "finder@test.mmu.edu.my",
      "rfid_tag": "TEST001",
      "phone": "+60123456789"
    }
  ],
  "collectors": [
    {
      "name": "Test Collector", 
      "email": "collector@test.mmu.edu.my",
      "student_id": "TEST123",
      "phone": "+60987654321"
    }
  ]
}
```

**Test Items:**
```json
{
  "items": [
    {
      "filename": "test_water_bottle.jpg",
      "description": "Blue plastic water bottle",
      "location_found": "Library",
      "finder_id": 1
    }
  ]
}
```

## 🔧 Performance Testing

### Load Testing

**Test Concurrent Users:**
```python
import threading
import requests
import time

def load_test_search():
    """Simulate concurrent search requests"""
    def search_worker():
        response = requests.post(
            'http://localhost:5000/search',
            json={'query': 'test item'}
        )
        return response.status_code == 200

    # Run 10 concurrent searches
    threads = []
    for i in range(10):
        t = threading.Thread(target=search_worker)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    print("✓ Load test completed")
```

**Performance Benchmarks:**
```bash
# Time API responses
time curl -X POST http://localhost:5000/search \
  -d '{"query":"test"}' \
  -H "Content-Type: application/json"

# Expected: < 2 seconds for typical searches
```

### Memory and Resource Testing

```bash
# Monitor system resources during tests
top -p $(pgrep -f "python.*app.py")

# Check database performance
sqlite3 backend/lost_and_found.db ".timer ON" "SELECT COUNT(*) FROM FOUND_ITEMS;"
```

## 🐛 Debugging Test Failures

### Common Test Failures

**Database Connection Issues:**
```
Error: database is locked
Solution: Ensure no other processes are using the database
```

**File Permission Errors:**
```
Error: Permission denied when copying files
Solution: Check write permissions on uploads/ and collectors/ folders
```

**API Endpoint Not Found:**
```
Error: 404 Not Found
Solution: Ensure Flask server is running and endpoints are registered
```

### Debugging Techniques

**Enable Debug Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run tests with verbose output
python -v tests/test_collect.py
```

**Database Debugging:**
```bash
# Check database contents
sqlite3 backend/lost_and_found.db
.tables
.schema FOUND_ITEMS
SELECT * FROM FOUND_ITEMS LIMIT 5;
```

**API Debugging:**
```bash
# Test with curl verbose mode
curl -v -X POST http://localhost:5000/upload \
  -F "image=@test.jpg"

# Check server logs
tail -f app.log
```

## 📈 Test Coverage

### Measuring Code Coverage

```bash
# Install coverage tool
pip install coverage

# Run tests with coverage
coverage run --source=backend tests/run_tests.py
coverage report
coverage html  # Generate HTML report
```

**Coverage Goals:**
- **API Endpoints**: 95%+ coverage
- **Database Operations**: 90%+ coverage  
- **Core Business Logic**: 95%+ coverage
- **Error Handling**: 80%+ coverage

### Coverage Report Analysis

**Good Coverage Example:**
```
Name                 Stmts   Miss  Cover
----------------------------------------
backend/app.py          45      2    96%
backend/database.py     67      5    93%
backend/routes/box.py   89      8    91%
----------------------------------------
TOTAL                  201     15    93%
```

**Areas Needing Improvement:**
- Error handling paths
- Edge case scenarios
- Hardware integration mocks

## 🏆 Test Best Practices

### Writing Effective Tests

**Test Structure:**
```python
def test_feature():
    """Test description explaining what is being tested"""
    # Arrange: Set up test data and conditions
    setup_test_environment()
    
    # Act: Execute the function being tested
    result = function_under_test(input_data)
    
    # Assert: Verify the expected outcome
    assert result == expected_value
    assert no_side_effects_occurred()
    
    # Cleanup: Remove test data
    cleanup_test_environment()
```

**Test Naming Convention:**
- `test_[feature]_[condition]_[expected_result]`
- Examples: `test_upload_valid_image_returns_success`
- Examples: `test_search_no_results_returns_empty_array`

### Continuous Integration

**Pre-commit Testing:**
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run tests before allowing commit
python tests/run_tests.py
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

echo "All tests passed. Commit proceeding."
```

**Automated Testing Pipeline:**
```yaml
# .github/workflows/test.yml
name: FINDR Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: python tests/run_tests.py
```

## 🔍 Test Environment Setup

### Local Development Testing

**Setup Script:**
```bash
#!/bin/bash
# setup_test_env.sh

# Create test directory structure
mkdir -p tests/test_images tests/test_data

# Copy sample test files
cp backend/uploads/sample_item.jpg tests/test_images/

# Initialize test database
python backend/db_manager.py --init --test

# Start test server
python backend/app.py --test-mode &

echo "Test environment ready"
```

### Docker Test Environment

**Dockerfile.test:**
```dockerfile
FROM python:3.8-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "tests/run_tests.py"]
```

**Run Tests in Docker:**
```bash
# Build test container
docker build -f Dockerfile.test -t findr-tests .

# Run tests
docker run --rm findr-tests
```

## 📚 Integration with Other Systems

### Testing External Dependencies

**Mock External Services:**
```python
from unittest.mock import patch, MagicMock

@patch('clip_utils.get_image_embedding')
def test_upload_with_mock_ai(mock_embedding):
    """Test upload without requiring actual AI processing"""
    mock_embedding.return_value = MagicMock()
    
    # Test upload functionality
    result = upload_image(test_file)
    assert result['status'] == 'success'
```

**Database Migration Testing:**
```bash
# Test migration from old format
python tests/test_migration.py

# Verify data integrity after migration
python tests/verify_migration.py
```

---

## 📚 Related Documentation

- **[API Guide](api-guide.md)**: Test API endpoints and expected responses
- **[Database Guide](database-guide.md)**: Database testing and validation
- **[Box Guide](box-guide.md)**: Hardware testing procedures

For additional testing utilities and examples, see the `tests/` directory and `tests/README.md`.