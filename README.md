# FINDR. - Lost & Found Made Easy (3rd Place Winner, Hardware Track, Code Nection MMU 2025)

FINDR is a smart automated box + AI-powered web app that simplifies the lost-and-found process on university campuses. Users can deposit found items securely and owners can search, match, and retrieve their belongings through an AI-driven system with RFID-based authentication.

## 🚀 Key Features

- 📷 Accessibility – Easy item drop off and easy item search anytime, anywhere
- 🤖 AI Matching – Lost item descriptions are matched with stored items using CLIP embeddings + LLM (Gemini 2.5 Flash).
- 🔐 24/7 Secure Retrieval – RFID card authentication ensures only the rightful owner can unlock the box.
- 📊 Transparency – Snapshots and logs track every deposit and retrieval.
- 🌍 Scalability – Multiple FINDR boxes can be deployed across campus, making it very accessible for students to drop-off/collect anywhere
- 🛠️ Modular Design – Easy to maintain and upgrade with modular hardware components.


## 🛠️ Hardware Components used in the final prototype

- ESP32-CAM - Captures images and handles communication with the server.
- LCD Display (LCD1) - Displays QR code for user login and shows the status of the box.
- PCF8575 I/O - Provides 16 additional GPIO pins to the ESP32 via I2C for connecting to low-speed devices.
- IR Sensor - Detects presence or movement of a person in front of the box.
- RFID Sensor - Allows users to unlock the box using their student card.
- Switch Sensor - Detects whether the box is open or closed.
- DC-DC Step-Down Converter - Provides regulated power supply to the entire circuit.

## 📺 Prototype Video
[![Watch the video](https://img.youtube.com/vi/-d-M06xUAgM/0.jpg)](https://youtu.be/-d-M06xUAgM)

## 📑 Prototype Slides
[View the full report (PDF)](./Team_Googol_Slides.pdf)

## Final Demo Video
[![Watch the final demo video](https://img.youtube.com/vi/GA4SrxnzHnM/0.jpg)](https://youtu.be/GA4SrxnzHnM)


## Quick Start

- Python Version : Python 3.10.12

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
- **[System Architecture](docs/system-architecture-diagram.md)** - Complete system overview with separated user flow

## Presentation Deck

- **[Flow Chart](https://www.mermaidchart.com/app/projects/dd0eea15-bc63-4a02-a0c7-3440051f175d/diagrams/5ef3004c-5b21-40b7-9589-12ee9d861a6f/version/v0.1/edit)** - Complete System Flow Chart

- **[Item upload and query pipeline](https://www.mermaidchart.com/app/projects/a605fc72-a4c5-45d0-abd0-827c4456da58/diagrams/9ac1802e-2a3a-4f5b-bafa-9e888fa3b06f/version/v0.1/edit)** - How we implement AI in image processing/query

- **[Schematic Diagram](docs/FINDR_schematic_diagram.jpg)** - Schematic Diagram for this diagram