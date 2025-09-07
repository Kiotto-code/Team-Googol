# FINDR - Smart Lost & Found System

FINDR is a smart automated box + AI-powered web app that simplifies the lost-and-found process on university campuses. Users can deposit found items securely and owners can search, match, and retrieve their belongings through an AI-driven system with RFID-based authentication.

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

## 🚀 Key Features

📷 Accessibility – Easy item drop off and easy item search anytime, anywhere
🤖 AI Matching – Lost item descriptions are matched with stored items using CLIP embeddings + ChromaDB.
🔐 Secure Retrieval – RFID card authentication ensures only the rightful owner can unlock the box.
📊 Transparency – Snapshots and logs track every deposit and retrieval.
🌍 Scalability – Multiple FINDR boxes can be deployed across campus.

## 🛠️ Hardware Components

ESP32-CAM - Captures images and handles communication with the server.
LCD Display (LCD1) - Displays QR code for user login and shows the status of the box.
PCF8575 I/O - Provides 16 additional GPIO pins to the ESP32 via I2C for connecting to low-speed devices.
IR Sensor - Detects presence or movement of a person in front of the box.
Ultrasonic Sensor - Detects and measures items placed inside the box.
RFID Sensor - Allows users to unlock the box using their student card.
Switch Sensor - Detects whether the box is open or closed.
Buzzer - Alerts the user if the box remains open.
DC-DC Step-Down Converter - Provides regulated power supply to the entire circuit.

## 📺 Prototype Video
[![Watch the video](https://img.youtube.com/vi/-d-M06xUAgM/0.jpg)](https://youtu.be/-d-M06xUAgM)

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
