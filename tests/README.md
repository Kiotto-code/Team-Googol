# Tests and Utilities

This folder contains testing scripts and utility tools for the Lost & Found system.

## Testing Scripts

### `test_collect.py`
Tests the collection functionality including:
- Database operations for collected items
- File system operations for collector folder
- Integration tests for the collect endpoint

**Usage:**
```bash
cd /home/MMU-hack/ticket
python tests/test_collect.py
```

## Utility Scripts

### `migrate_data.py`
Migration utility to convert data from `data.json` format to SQLite database.

**Usage:**
```bash
cd /home/MMU-hack/ticket
python tests/migrate_data.py
```

### `api_utils.py`
Standardized API response utilities (currently unused in main app).
Contains helper functions for consistent API responses:
- `success_response()` - Standardized success responses
- `error_response()` - Standardized error responses  
- `paginated_response()` - Paginated data responses

This utility can be used for future API standardization.

## Running Tests

To run all tests manually:

1. **Collect Tests:**
   ```bash
   python tests/test_collect.py
   ```

2. **API Tests (curl):**
   ```bash
   # Test collect endpoint
   curl -X POST http://127.0.0.1:5000/collect \
     -F "image=@backend/uploads/shopping.webp" \
     -F "timestamp=$(date +%s)" \
     -F "box_id=test_box"
   ```

## File Organization

- `test_*.py` - Unit and integration test files
- `migrate_*.py` - Migration and utility scripts
- `__init__.py` - Tests package initialization
