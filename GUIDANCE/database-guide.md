# Database Guide - FINDR System

This guide covers the database schema, management tools, migration procedures, and troubleshooting for the FINDR Smart Lost & Found system.

## 🗄️ Database Overview

FINDR uses **SQLite** as its primary database for simplicity and reliability:

- **Database File**: `lost_and_found.db`
- **Location**: Project root directory
- **Backup Location**: `backend/lost_and_found.db` (alternative)
- **Engine**: SQLite 3.x
- **Management**: Python `sqlite3` module

## 📊 Database Schema

### Core Tables

#### 1. FINDERS Table
Stores information about people who found items.

```sql
CREATE TABLE FINDERS (
    finder_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    rfid_tag TEXT UNIQUE,
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Key Fields:**
- `finder_id`: Unique identifier for finder
- `rfid_tag`: RFID card ID for authentication
- `email`: Used for notifications and identification

#### 2. COLLECTORS Table
Stores information about people claiming items.

```sql
CREATE TABLE COLLECTORS (
    collector_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,  
    phone TEXT,
    student_id TEXT UNIQUE,
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Key Fields:**
- `collector_id`: Unique identifier for collector
- `student_id`: Student ID for verification
- `email`: Used for claim notifications

#### 3. FOUND_ITEMS Table
Main table for lost items uploaded to the system.

```sql
CREATE TABLE FOUND_ITEMS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    description TEXT,
    image_embedding TEXT NOT NULL,          -- CLIP image embedding
    description_embedding TEXT,             -- CLIP text embedding  
    status TEXT DEFAULT 'available',       -- available, claimed, collected
    claimed_at DATETIME,
    claimed_by INTEGER,                     -- References COLLECTORS.collector_id
    finder_id INTEGER,                      -- References FINDERS.finder_id
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,                    -- Claim expiry time
    FOREIGN KEY (claimed_by) REFERENCES COLLECTORS (collector_id),
    FOREIGN KEY (finder_id) REFERENCES FINDERS (finder_id)
);
```

**Status Values:**
- `available`: Item is searchable and can be claimed
- `claimed`: Item is claimed but not yet collected
- `collected`: Item has been physically collected

#### 4. COLLECTED_ITEMS Table
Archives of items that have been physically collected.

```sql
CREATE TABLE COLLECTED_ITEMS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    box_id TEXT,                           -- Collection box identifier
    finder_id INTEGER,                     -- References FINDERS.finder_id
    imgtaken_timestamp REAL,               -- When collection photo was taken
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (finder_id) REFERENCES FINDERS (finder_id)
);
```

#### 5. BOX Table
Hardware box management and status.

```sql
CREATE TABLE BOX (
    id TEXT PRIMARY KEY,                   -- Box identifier (e.g., "box_001")
    status TEXT DEFAULT 'available',       -- available, full, collect_request, etc.
    door_status TEXT DEFAULT 'closed',     -- closed, open
    capacity INTEGER DEFAULT 1,            -- Maximum items (usually 1)
    current_load INTEGER DEFAULT 0,        -- Current item count
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Database Relationships

```
FINDERS (1) ──── (many) FOUND_ITEMS
COLLECTORS (1) ──── (many) FOUND_ITEMS (claimed_by)
FINDERS (1) ──── (many) COLLECTED_ITEMS
BOX (1) ──── (many) COLLECTED_ITEMS
```

## 🔧 Database Management

### CLI Database Manager

The system includes a command-line tool for database management:

```bash
# Navigate to backend directory
cd backend

# Display help
python db_manager.py --help
```

**Available Commands:**

```bash
# Initialize database (create tables)
python db_manager.py --init

# List all items
python db_manager.py list

# List only available items  
python db_manager.py list --available

# Get system statistics
python db_manager.py stats

# Clear all items (destructive!)
python db_manager.py clear

# Release expired claims
python db_manager.py release-expired
```

### Database Initialization

**First-time Setup:**
```bash
# Initialize all tables and schema
python backend/db_manager.py --init

# Verify initialization
python backend/db_manager.py stats
```

**Expected Output:**
```
Database initialized successfully
Tables created: FINDERS, COLLECTORS, FOUND_ITEMS, COLLECTED_ITEMS, BOX
```

### Viewing Database Contents

**List Items:**
```bash
# All items with full details
python backend/db_manager.py list
```

**Sample Output:**
```
All Items:
--------------------------------------------------------------------------------
ID: 1
Filename: water_bottle_001.jpg
Description: Blue plastic water bottle found in library
Status: available
Uploaded: 2025-09-20 10:30:00
--------------------------------------------------------------------------------
ID: 2  
Filename: keys_002.jpg
Description: Set of keys with red keychain
Status: claimed
Claimed by: 5
Claimed at: 2025-09-20 14:15:00
Expires at: 2025-09-21 14:15:00
--------------------------------------------------------------------------------
```

**Statistics Overview:**
```bash
python backend/db_manager.py stats
```

**Sample Output:**
```
=== FINDR System Statistics ===
Total Items: 15
Available Items: 8
Claimed Items: 5  
Collected Items: 2
Total Finders: 12
Total Collectors: 8
Total Boxes: 3
Active Claims: 3
```

## 🔄 Database Migrations

### Automatic Migration System

The system includes automatic migration for schema updates:

```python
def migrate_user_references():
    """Migrate existing user references to new separated table structure."""
    # Automatically called during init_database()
    # Handles schema updates without data loss
```

**Migration Features:**
- **Backward Compatibility**: Old data is preserved
- **Column Type Changes**: TEXT to INTEGER conversions
- **New Column Addition**: Safely adds missing columns
- **Data Validation**: Ensures data integrity during migration

### Manual Migration

**For Major Schema Changes:**
```bash
# Backup current database
cp lost_and_found.db lost_and_found.db.backup

# Run migration script
python tests/migrate_data.py

# Verify migration success
python backend/db_manager.py stats
```

**Migration from Old JSON Format:**
```bash
# If upgrading from file-based storage
python tests/migrate_data.py --from-json data.json --to-sqlite lost_and_found.db
```

## 🔍 Database Operations

### Direct SQL Access

**Connect to Database:**
```bash
# Open SQLite command line
sqlite3 lost_and_found.db

# Show tables
.tables

# Show schema for specific table
.schema FOUND_ITEMS

# Query examples
SELECT * FROM FOUND_ITEMS WHERE status = 'available';
SELECT COUNT(*) FROM COLLECTORS;
```

### Python Database Operations

**Basic Operations:**
```python
import sqlite3

# Connect to database
conn = sqlite3.connect('lost_and_found.db')
cursor = conn.cursor()

# Query items
cursor.execute("SELECT * FROM FOUND_ITEMS WHERE status = ?", ('available',))
items = cursor.fetchall()

# Insert new item
cursor.execute("""
    INSERT INTO FOUND_ITEMS (filename, description, image_embedding, finder_id)
    VALUES (?, ?, ?, ?)
""", (filename, description, embedding, finder_id))

conn.commit()
conn.close()
```

**Using Context Manager:**
```python
from database import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM FOUND_ITEMS")
    count = cursor.fetchone()[0]
    print(f"Total items: {count}")
```

### Advanced Queries

**Search Operations:**
```sql
-- Find items by description
SELECT * FROM FOUND_ITEMS 
WHERE description LIKE '%water bottle%' 
AND status = 'available';

-- Items claimed but not collected
SELECT fi.*, c.name, c.email 
FROM FOUND_ITEMS fi
JOIN COLLECTORS c ON fi.claimed_by = c.collector_id
WHERE fi.status = 'claimed';

-- Items by specific finder
SELECT fi.*, f.name as finder_name
FROM FOUND_ITEMS fi  
JOIN FINDERS f ON fi.finder_id = f.finder_id
WHERE f.email = 'john@student.mmu.edu.my';
```

**Box Status Queries:**
```sql
-- Box utilization
SELECT id, status, current_load, capacity,
       (CAST(current_load AS FLOAT) / capacity * 100) as utilization
FROM BOX;

-- Boxes needing collection
SELECT * FROM BOX 
WHERE status = 'collect_request';
```

## 🛠️ Database Maintenance

### Regular Maintenance Tasks

**Daily Tasks:**
```bash
# Release expired claims (run daily)
python backend/db_manager.py release-expired

# Check system health
python backend/db_manager.py stats
```

**Weekly Tasks:**
```bash
# Database backup
cp lost_and_found.db backups/backup_$(date +%Y%m%d).db

# Optimize database
sqlite3 lost_and_found.db "VACUUM;"
```

**Monthly Tasks:**
```bash
# Analyze database performance
sqlite3 lost_and_found.db "ANALYZE;"

# Check for orphaned records
sqlite3 lost_and_found.db "PRAGMA foreign_key_check;"
```

### Performance Optimization

**Create Indexes:**
```sql
-- Speed up search operations
CREATE INDEX IF NOT EXISTS idx_found_items_status ON FOUND_ITEMS(status);
CREATE INDEX IF NOT EXISTS idx_found_items_filename ON FOUND_ITEMS(filename);
CREATE INDEX IF NOT EXISTS idx_finders_rfid ON FINDERS(rfid_tag);
CREATE INDEX IF NOT EXISTS idx_collectors_student_id ON COLLECTORS(student_id);

-- Speed up join operations  
CREATE INDEX IF NOT EXISTS idx_found_items_finder ON FOUND_ITEMS(finder_id);
CREATE INDEX IF NOT EXISTS idx_found_items_collector ON FOUND_ITEMS(claimed_by);
```

**Database Size Management:**
```bash
# Check database size
du -h lost_and_found.db

# Archive old collected items
sqlite3 lost_and_found.db "
DELETE FROM COLLECTED_ITEMS 
WHERE uploaded_at < date('now', '-6 months');
"
```

## 🚨 Troubleshooting

### Common Issues

#### Database Locked Error
```
Error: database is locked
```

**Solutions:**
```bash
# Check for running processes
lsof lost_and_found.db

# Kill blocking processes
pkill -f "python.*app.py"

# Wait and retry
sleep 5 && python backend/db_manager.py stats
```

#### Missing Tables
```
Error: no such table: FOUND_ITEMS
```

**Solution:**
```bash
# Re-initialize database
python backend/db_manager.py --init
```

#### Foreign Key Constraint Errors
```
Error: FOREIGN KEY constraint failed
```

**Debug Steps:**
```sql
-- Enable foreign key checking
PRAGMA foreign_keys = ON;

-- Check constraint violations
PRAGMA foreign_key_check;

-- Find orphaned records
SELECT * FROM FOUND_ITEMS 
WHERE finder_id NOT IN (SELECT finder_id FROM FINDERS);
```

#### Corrupted Database
```
Error: database disk image is malformed
```

**Recovery Steps:**
```bash
# Create backup of corrupted database
cp lost_and_found.db corrupted_backup.db

# Attempt to dump and restore
sqlite3 corrupted_backup.db ".dump" | sqlite3 recovered.db

# Verify recovery
python backend/db_manager.py stats
```

### Performance Issues

**Slow Queries:**
```bash
# Enable query timing
sqlite3 lost_and_found.db
.timer ON
SELECT COUNT(*) FROM FOUND_ITEMS;
```

**Memory Issues:**
```bash
# Check database cache settings
sqlite3 lost_and_found.db "PRAGMA cache_size;"

# Increase cache size (in pages)
sqlite3 lost_and_found.db "PRAGMA cache_size = 10000;"
```

## 🔒 Data Security

### Backup Strategies

**Automated Backup Script:**
```bash
#!/bin/bash
# backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"
DB_FILE="lost_and_found.db"

mkdir -p $BACKUP_DIR

# Create backup
cp $DB_FILE $BACKUP_DIR/backup_$DATE.db

# Compress backup
gzip $BACKUP_DIR/backup_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.db.gz" -mtime +30 -delete

echo "Backup completed: backup_$DATE.db.gz"
```

**Run Backup:**
```bash
# Make executable
chmod +x backup_database.sh

# Run backup
./backup_database.sh

# Schedule daily backups (crontab)
0 2 * * * /path/to/backup_database.sh
```

### Data Privacy

**Sensitive Data Handling:**
- **Embeddings**: Stored as text but contain no personal info
- **Images**: Store filenames only, not actual image data
- **User Info**: Email and RFID hashed in production
- **Logs**: Avoid logging personal information

**Data Retention:**
```sql
-- Remove old collected items (>1 year)
DELETE FROM COLLECTED_ITEMS 
WHERE uploaded_at < date('now', '-1 year');

-- Anonymize old user records
UPDATE FINDERS 
SET email = 'anonymized@example.com', 
    phone = NULL 
WHERE registration_date < date('now', '-2 years');
```

## 📈 Monitoring and Analytics

### Database Health Monitoring

**Monitor Script:**
```python
import sqlite3
from datetime import datetime

def check_database_health():
    """Check database health and report issues"""
    with sqlite3.connect('lost_and_found.db') as conn:
        cursor = conn.cursor()
        
        # Check table integrity
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        
        # Check foreign key constraints
        cursor.execute("PRAGMA foreign_key_check") 
        fk_violations = cursor.fetchall()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM FOUND_ITEMS")
        total_items = cursor.fetchone()[0]
        
        print(f"Database Health Check - {datetime.now()}")
        print(f"Integrity: {integrity}")
        print(f"Foreign Key Violations: {len(fk_violations)}")
        print(f"Total Items: {total_items}")
        
        return integrity == 'ok' and len(fk_violations) == 0

if __name__ == "__main__":
    healthy = check_database_health()
    exit(0 if healthy else 1)
```

### Usage Analytics

**Generate Reports:**
```python
def generate_usage_report():
    """Generate usage statistics report"""
    with sqlite3.connect('lost_and_found.db') as conn:
        cursor = conn.cursor()
        
        # Items uploaded per day (last 30 days)
        cursor.execute("""
            SELECT DATE(uploaded_at) as date, COUNT(*) as count
            FROM FOUND_ITEMS 
            WHERE uploaded_at >= date('now', '-30 days')
            GROUP BY DATE(uploaded_at)
            ORDER BY date DESC
        """)
        daily_uploads = cursor.fetchall()
        
        # Most active finders
        cursor.execute("""
            SELECT f.name, COUNT(fi.id) as items_found
            FROM FINDERS f
            JOIN FOUND_ITEMS fi ON f.finder_id = fi.finder_id
            GROUP BY f.finder_id, f.name
            ORDER BY items_found DESC
            LIMIT 10
        """)
        top_finders = cursor.fetchall()
        
        # Generate report
        print("=== FINDR Usage Report ===")
        print("\nDaily Uploads (Last 30 Days):")
        for date, count in daily_uploads:
            print(f"{date}: {count} items")
            
        print("\nTop Finders:")
        for name, count in top_finders:
            print(f"{name}: {count} items found")
```

---

## 📚 Related Documentation

- **[API Guide](api-guide.md)**: Database-related API endpoints
- **[Testing Guide](testing-guide.md)**: Database testing procedures
- **[Box Guide](box-guide.md)**: Box table management

For database schema diagrams and additional details, see `docs/database-diagram.md`.