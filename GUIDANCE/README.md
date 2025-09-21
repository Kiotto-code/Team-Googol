# GUIDANCE - FINDR System Documentation Hub

Welcome to the FINDR Smart Lost & Found System guidance documentation. This folder contains comprehensive guides to help you understand, use, develop, and maintain the FINDR system.

## 📖 What is FINDR?

FINDR is a smart automated lost-and-found system designed for university campuses. It combines:
- **Smart Hardware Boxes** for secure item storage
- **AI-Powered Matching** using CLIP embeddings and ChromaDB
- **RFID Authentication** for secure item retrieval
- **Web Interface** for easy search and management

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8+
- SQLite3
- Required packages: `pip install -r requirements.txt`

### Basic Setup
1. **Clone and Setup:**
   ```bash
   cd /home/chan/work/ticket
   pip install -r requirements.txt
   ```

2. **Initialize Database:**
   ```bash
   python backend/db_manager.py --init
   ```

3. **Start Backend:**
   ```bash
   python backend/app.py
   ```

4. **Access System:**
   - Web Interface: `http://localhost:5000`
   - API Base: `http://localhost:5000/api`

## 📚 Documentation Guide Map

### 🔧 For Developers & System Administrators

- **[API Guide](api-guide.md)** - Complete API reference with examples
- **[Box Guide](box-guide.md)** - Box management and hardware integration
- **[Database Guide](database-guide.md)** - Schema, migrations, and management
- **[Testing Guide](testing-guide.md)** - How to run and interpret tests

### 📋 For End Users

- **Web Interface:** Open `frontend/index.html` for the user interface
- **Mobile Access:** System is mobile-responsive
- **RFID Cards:** Required for item collection authentication

## 🏗️ System Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Hardware Box  │    │   Web Frontend  │    │  Mobile Access  │
│   (RFID + ESP)  │◄───┤  (HTML/JS/CSS)  │◄───┤   (Browser)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Flask Backend  │
                    │   (Python API)  │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   SQLite DB +   │
                    │   ChromaDB AI   │
                    └─────────────────┘
```

## 🔄 System Workflow

1. **Item Drop-off:**
   - User finds lost item → Deposits in FINDR box
   - System captures image → AI processes with CLIP embeddings
   - Item stored in database with metadata

2. **Item Search:**
   - Owner searches via web/mobile interface
   - AI matches description/image against stored items
   - System returns ranked results

3. **Item Collection:**
   - Owner presents RFID card for authentication
   - Box opens automatically upon verification
   - System logs collection and updates status

## 🎯 Key Features

- **📷 Accessibility:** Easy drop-off and search anytime, anywhere
- **🤖 AI Matching:** CLIP embeddings + ChromaDB for intelligent search
- **🔐 Secure Retrieval:** RFID authentication ensures rightful ownership
- **📊 Transparency:** Complete audit trail of deposits and collections
- **🌍 Scalability:** Multi-box deployment across campus locations

## 📁 Project Structure

```
├── backend/              # Flask API server
│   ├── routes/          # API endpoint definitions
│   │   ├── box.py       # Box management endpoints
│   │   ├── upload.py    # Item upload handling
│   │   ├── search.py    # AI-powered search
│   │   └── collect.py   # Collection workflow
│   ├── uploads/         # Uploaded item images
│   ├── collectors/      # Collected item archives
│   └── *.py            # Core modules (database, AI, utils)
├── frontend/            # Web interface
├── hardware/            # ESP32/Arduino code
├── docs/               # Additional documentation
├── tests/              # Test suite and utilities
└── GUIDANCE/           # This documentation hub
```

## 🔧 Common Operations

### For Daily Operations:
- **Check System Status:** `python backend/db_manager.py stats`
- **View All Boxes:** `curl http://localhost:5000/boxes`
- **Manual Collection:** Use web interface or direct API calls

### For Development:
- **Run Tests:** `python tests/run_tests.py`
- **Database Reset:** `python backend/db_manager.py clear`
- **View Logs:** Check terminal output or implement logging

### For Troubleshooting:
- **Database Issues:** See [Database Guide](database-guide.md)
- **API Problems:** See [API Guide](api-guide.md)
- **Box Hardware:** See [Box Guide](box-guide.md)

## 🆘 Getting Help

1. **Check Specific Guides:** Use the documentation links above
2. **Run Tests:** `python tests/run_tests.py` to verify system health
3. **Check Logs:** Review terminal output for error messages
4. **Database Status:** `python backend/db_manager.py list` to view current state

## 📝 Contributing

When making changes:
1. **Test First:** Run `python tests/run_tests.py`
2. **Update Documentation:** Keep guides current with changes
3. **Follow Structure:** Maintain the established project organization
4. **Validate APIs:** Test endpoints after modifications

---

**Next Steps:** Choose a specific guide above based on your needs, or continue with the [API Guide](api-guide.md) for technical integration details.