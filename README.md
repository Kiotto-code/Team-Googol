# Lost & Found System

A web-based lost and found system using CLIP embeddings for intelligent image search, with separated user management for finders and collectors.

## Project Structure

```
├── backend/           # Backend Flask application
│   ├── routes/        # API routes (with separated user management)
│   ├── uploads/       # Uploaded lost item images
│   ├── collectors/    # Collected item images
│   └── *.py          # Core backend modules
├── frontend/          # Frontend HTML/JS application
├── docs/             # Complete system documentation
├── tests/            # Testing scripts and utilities
└── requirements.txt  # Python dependencies
```

## Key Features

- **Separated User Management**: Distinct FINDERS and COLLECTORS tables with role-specific features
- **RFID Integration**: Quick finder identification via RFID tags
- **Student ID Support**: University system integration for collectors
- **Smart Search**: CLIP-powered visual and text search with user attribution
- **Collection System**: API for automated item collection with finder tracking
- **Reputation System**: Track finder reliability and collector verification status

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

### User Management (Separated)
- `POST /finder/register` - Register a new finder with RFID
- `POST /collector/register` - Register a new collector with student ID
- `GET /finder/rfid/<tag>` - Quick finder lookup by RFID
- `GET /user/search` - Cross-table user search by email

### Item Management
- `POST /upload` - Upload a lost item image (with finder reference)
- `POST /search` - Search for items using image or text
- `POST /collect` - Collect found items (with RFID integration)
- `POST /claim` - Claim a found item (with collector verification)
- `DELETE /delete/<filename>` - Delete an item

### System Statistics
- `GET /users/stats` - Get system-wide user statistics

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

The system uses separated user management with automatic migration:

```bash
# Database CLI tools
python backend/db_manager.py --help
python backend/db_manager.py list
python backend/db_manager.py clear

# Manual migration (if needed)
python backend/migrate_data.py
```

### Database Schema (Updated)
- **FINDERS**: Separate table for people who find items (with RFID support)
- **COLLECTORS**: Separate table for people claiming items (with student ID)
- **FOUND_ITEMS**: Links to both FINDERS (finder_id) and COLLECTORS (claimed_by)
- **COLLECTED_ITEMS**: References FINDERS for collection tracking

## Documentation

Complete documentation is available in the `docs/` folder:
- **[Item Status Guide](docs/item-status-guide.md)** - Updated user management and item lifecycle
- **[Box Status Guide](docs/box-status-guide.md)** - Physical box management
- **[System Architecture](system-architecture-diagram.md)** - Complete system overview with separated user flow

## Features

- **Separated User Management**: FINDERS and COLLECTORS tables with specific roles
- **RFID Integration**: Quick finder identification and tracking
- **Student ID Support**: University integration for collector verification
- **Smart Search**: CLIP-powered visual and text search with user attribution
- **Collection System**: API for automated item collection with finder tracking
- **Claim Management**: Temporary claims with automatic expiration
- **Reputation System**: Track finder reliability and collector verification status
- **Foreign Key Relationships**: Proper database relationships between users and items
- **Image Processing**: Secure file handling and storage
- **Database Migration**: Automatic upgrade from single USERS table to separated architecture
