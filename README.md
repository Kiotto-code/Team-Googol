# Lost & Found System

A web-based lost and found system using CLIP embeddings for intelligent image search.

## Project Structure

```
├── backend/           # Backend Flask application
│   ├── routes/        # API routes
│   ├── uploads/       # Uploaded lost item images
│   ├── collectors/    # Collected item images
│   └── *.py          # Core backend modules
├── frontend/          # Frontend HTML/JS application
├── tests/            # Testing scripts and utilities
└── requirements.txt  # Python dependencies
```

## Quick Start

1. **Setup Environment:**
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Start Backend:**
   ```bash
   cd backend
   python app.py
   ```

3. **Open Frontend:**
   Open `frontend/index.html` in a web browser

## API Endpoints

- `POST /upload` - Upload a lost item image
- `POST /search` - Search for items using image or text
- `POST /collect` - Collect found items (for collection system)
- `POST /claim` - Claim a found item
- `DELETE /delete/<filename>` - Delete an item

## Testing

All testing scripts are located in the `tests/` folder:

```bash
# Run all tests
python tests/run_tests.py

# Run specific tests
python tests/test_collect.py

# Run migration utility
python tests/migrate_data.py
```

See `tests/README.md` for detailed testing documentation.

## Database Management

Use the database manager CLI tool:

```bash
python backend/db_manager.py --help
python backend/db_manager.py list
python backend/db_manager.py clear
```

## Features

- **Smart Search**: CLIP-powered visual and text search
- **Collection System**: API for automated item collection
- **Claim Management**: Temporary claims with automatic expiration
- **Image Processing**: Secure file handling and storage
- **Database**: SQLite with proper data modeling
