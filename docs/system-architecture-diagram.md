# Lost & Found Ticket System - Updated Architecture Flow Diagram

## System Overview with Separated User Management
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          LOST & FOUND TICKET SYSTEM                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   FINDER    │    │  COLLECTOR  │    │ COLLECTOR   │    │    ADMIN    │     │
│  │ (Person who │    │  (System)   │    │ (Person who │    │   (User)    │     │
│  │finds items) │    │             │    │lost items)  │    │             │     │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │                   │          │
│         ▼                   ▼                   ▼                   ▼          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    WEB APPLICATION (Flask)                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │  │                      API ROUTES                                │   │   │
│  │  │ /finder/* /collector/* /upload /search /claim /collect /box   │   │   │
│  │  └─────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                           │
│                                    ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      DATABASE LAYER                                    │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │   │
│  │  │   FINDERS    │ │ COLLECTORS   │ │ FOUND_ITEMS  │ │    BOXES     │  │   │
│  │  │              │ │              │ │              │ │              │  │   │
│  │  │finder_id(PK) │ │collector_id  │ │ id (PK)      │ │ id (PK)      │  │   │
│  │  │name          │ │(PK)          │ │ filename     │ │ status       │  │   │
│  │  │email         │ │name          │ │ description  │ │ door_status  │  │   │
│  │  │rfid_tag      │ │email         │ │ embeddings   │ │ capacity     │  │   │
│  │  │items_found   │ │student_id    │ │ status       │ │ current_load │  │   │
│  │  │reputation    │ │items_claimed │ │ claimed_by   │ │ last_updated │  │   │
│  │  │created_at    │ │verification  │ │ finder_id    │ │              │  │   │
│  │  └──────────────┘ │created_at    │ │ uploaded_at  │ └──────────────┘  │   │
│  │                   └──────────────┘ └──────────────┘                   │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │   │
│  │  │              COLLECTED_ITEMS                                     │  │   │
│  │  │ id (PK) | filename | box_id | finder_id | timestamp | uploaded  │  │   │
│  │  └──────────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Updated User Management Flow

### 1. Separated User Registration
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           USER REGISTRATION FLOW                               │
└─────────────────────────────────────────────────────────────────────────────────┘

For FINDERS (People who find items):
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐
│   Person    │───▶│  Registration   │───▶│   Validation    │───▶│  FINDERS    │
│ Finds Item  │    │POST /finder/    │    │   Process       │    │   Table     │
│             │    │register         │    │                 │    │             │
└─────────────┘    └─────────────────┘    └─────────────────┘    └─────────────┘
       │                    │                       │                    │
       │                    ▼                       ▼                    ▼
       │           - name               Check unique           finder_id
       │           - email              email/rfid_tag        name, email
       │           - phone              Generate finder_id     rfid_tag
       │           - rfid_tag           RFID for quick ID      phone
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  FINDER FEATURES                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ • RFID tag support for quick identification                             │   │
│  │ • Item count tracking (items_found)                                     │   │
│  │ • Reputation score based on successful matches                          │   │
│  │ • Phone contact information                                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘

For COLLECTORS (People who lost items):
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐
│   Person    │───▶│  Registration   │───▶│   Validation    │───▶│ COLLECTORS  │
│ Lost Item   │    │POST /collector/ │    │   Process       │    │   Table     │
│             │    │register         │    │                 │    │             │
└─────────────┘    └─────────────────┘    └─────────────────┘    └─────────────┘
       │                    │                       │                    │
       │                    ▼                       ▼                    ▼
       │           - name               Check unique          collector_id
       │           - email              email/student_id     name, email
       │           - phone              Generate collector_id student_id
       │           - student_id         ID verification       phone
       │           - id_number
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  COLLECTOR FEATURES                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ • Student ID support for university systems                             │   │
│  │ • National ID number for verification                                   │   │
│  │ • Verification status tracking                                          │   │
│  │ • Items claimed count                                                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Updated Item Collection Flow
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     UPDATED ITEM COLLECTION FLOW                               │
└─────────────────────────────────────────────────────────────────────────────────┘

Step 1: Item Found by System or Person
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐
│  Physical   │───▶│   Collection    │───▶│   Image         │───▶│   Box       │
│   Item      │    │   System        │    │   Processing    │    │  Storage    │
│   Found     │    │   (Camera)      │    │   (CLIP AI)     │    │             │
└─────────────┘    └─────────────────┘    └─────────────────┘    └─────────────┘
       │                    │                       │                    │
       │                    ▼                       ▼                    ▼
       │           POST /collect              Generate               Update Box
       │           - image file              Embeddings              Status to
       │           - timestamp              - Image embedding         "full"
       │           - box_id                 - Text embedding         Set Load=1
       │           - finder_rfid (optional)  Store in DB             Update Finder
       │                                                            Stats if RFID
       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  COLLECTED_ITEMS Table (Updated)                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ id | filename | box_id | finder_id | timestamp | uploaded_at           │   │
│  │ 1  | item1.jpg| box_01 | 123 (FK)  | 167890... | 2025-09-01 10:30:00  │   │
│  │    |          |        | to FINDER |           |                       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Updated Claim & Collection Flow
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     UPDATED CLAIM & COLLECTION FLOW                            │
└─────────────────────────────────────────────────────────────────────────────────┘

Step 1: Collector Claims Item
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐
│ COLLECTOR   │───▶│  Claim Request  │───▶│   Validation    │───▶│  Box Door   │
│ (Lost Item  │    │  POST /claim    │    │   Process       │    │   Opens     │
│  Owner)     │    │                 │    │                 │    │             │
└─────────────┘    └─────────────────┘    └─────────────────┘    └─────────────┘
       │                    │                       │                    │
       │                    ▼                       ▼                    ▼
       │           - item_id            Update FOUND_ITEMS         Box Status:
       │           - collector_id       claimed_by: collector_id   "collect_request"
       │           - verification       Status: "claimed"          Door: "open"
       │                               Update Collector Stats     
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  UPDATED CLAIM TRACKING                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ FOUND_ITEMS.claimed_by → COLLECTORS.collector_id (INTEGER FK)           │   │
│  │ FOUND_ITEMS.finder_id → FINDERS.finder_id (INTEGER FK)                  │   │
│  │ Both Finder and Collector stats updated automatically                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Updated API Endpoints

### User Management APIs
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            USER MANAGEMENT APIs                                │
└─────────────────────────────────────────────────────────────────────────────────┘

FINDER APIs:
• POST /finder/register           - Register new finder
• GET  /finder/{id}              - Get finder details
• GET  /finder/rfid/{rfid}       - Find finder by RFID tag
• GET  /finders                  - Get all finders (admin)

COLLECTOR APIs:
• POST /collector/register        - Register new collector
• GET  /collector/{id}           - Get collector details  
• GET  /collector/student/{id}   - Find collector by student ID
• GET  /collectors               - Get all collectors (admin)

GENERAL USER APIs:
• GET  /user/search?email={email} - Search across both tables
• GET  /users/stats              - Get system user statistics
```

### Updated Integration Points
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         UPDATED SYSTEM INTEGRATION                             │
└─────────────────────────────────────────────────────────────────────────────────┘

Collection Endpoint (/collect):
- Now accepts finder_rfid parameter
- Looks up finder in FINDERS table by RFID
- Updates finder statistics (items_found, reputation)
- Stores finder_id in COLLECTED_ITEMS

Claim Endpoint (/claim):  
- Now requires collector_id instead of text name
- Updates COLLECTORS table statistics
- Foreign key relationship ensures data integrity

Search Results:
- Include finder information for transparency
- Show collector verification status
- Display reputation scores for trust
```

## Key Benefits of Separated User Management

### 1. **Data Integrity**
- Foreign key relationships ensure consistency
- No more text-based user references
- Proper normalization reduces redundancy

### 2. **Enhanced Features**
- RFID support for finders (quick identification)
- Student ID support for collectors (university integration)
- Reputation and verification systems

### 3. **Better Analytics**
- Separate statistics for finders vs collectors
- Track success rates and user engagement
- Identify top contributors and frequent claimers

### 4. **Scalability**
- Independent management of user types
- Role-specific attributes and features
- Easier to extend with additional user types

### 5. **Security & Verification**
- Collector verification status tracking
- Multiple identification methods
- Audit trail for all claims and finds

This updated architecture provides a robust foundation for managing different types of users while maintaining system efficiency and data integrity.