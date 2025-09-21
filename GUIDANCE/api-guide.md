# API Guide - FINDR System

This guide provides comprehensive documentation for the FINDR system's REST API endpoints, including request/response formats, authentication, and integration examples.

## 🔗 Base URL

```
http://localhost:5000
```

All API endpoints are relative to this base URL.

## 📋 API Overview

The FINDR API is organized into several main categories:

- **User Management**: Register and manage finders and collectors
- **Item Management**: Upload, search, claim, and collect items
- **Box Management**: Control and monitor hardware boxes
- **System Statistics**: Get system-wide information

## 🔐 Authentication

- **RFID Authentication**: Required for item collection
- **No API Keys**: Currently open API for development
- **Rate Limiting**: Not implemented (consider for production)

---

## 👥 User Management APIs

### Register a Finder (Person who found an item)

```http
POST /finder/register
```

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@student.mmu.edu.my", 
  "phone": "+60123456789",
  "rfid_tag": "ABC123456"
}
```

**Response:**
```json
{
  "message": "Finder registered successfully",
  "finder_id": 1,
  "name": "John Doe",
  "rfid_tag": "ABC123456"
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid data or missing fields
- `500`: Server error

### Register a Collector (Person claiming an item)

```http
POST /collector/register
```

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane@student.mmu.edu.my",
  "phone": "+60123456789", 
  "student_id": "STU001234"
}
```

**Response:**
```json
{
  "message": "Collector registered successfully",
  "collector_id": 1,
  "name": "Jane Smith",
  "student_id": "STU001234"
}
```

### Quick Finder Lookup by RFID

```http
GET /finder/rfid/{rfid_tag}
```

**Example:**
```bash
curl http://localhost:5000/finder/rfid/ABC123456
```

**Response:**
```json
{
  "finder_id": 1,
  "name": "John Doe",
  "email": "john@student.mmu.edu.my",
  "rfid_tag": "ABC123456",
  "registration_date": "2025-09-20T10:30:00"
}
```

### Cross-table User Search

```http
GET /user/search?email={email}
```

**Example:**
```bash
curl "http://localhost:5000/user/search?email=john@student.mmu.edu.my"
```

**Response:**
```json
{
  "found_in": "finder",
  "user_data": {
    "finder_id": 1,
    "name": "John Doe",
    "email": "john@student.mmu.edu.my"
  }
}
```

---

## 📦 Item Management APIs

### Upload a Lost Item

```http
POST /upload
```

**Content Type:** `multipart/form-data`

**Form Fields:**
- `image`: Image file (required)
- `description`: Optional user description
- `finder_id`: ID of the person who found the item

**Example using curl:**
```bash
curl -X POST http://localhost:5000/upload \
  -F "image=@/path/to/item.jpg" \
  -F "description=Blue water bottle found in library" \
  -F "finder_id=1"
```

**Response:**
```json
{
  "message": "Image uploaded successfully",
  "filename": "item_12345.jpg",
  "description": "Blue water bottle found in library",
  "gemini_caption": "Color: Blue; Type: Water bottle; Material: Plastic; Features: Sport cap, 500ml; Brand: Nike",
  "item_id": 42
}
```

**Validation Checks:**
- **Lighting Quality**: Checks brightness and contrast
- **Framing**: Ensures item is properly centered and visible
- **File Format**: Accepts common image formats (JPG, PNG, WEBP)

### Search for Items

```http
POST /search
```

**Request Body:**
```json
{
  "query": "blue water bottle nike"
}
```

**Response:**
```json
{
  "results": [
    {
      "filename": "item_12345.jpg",
      "description": "Blue water bottle found in library",
      "score": 0.85,
      "item_id": 42,
      "gemini_caption": "Color: Blue; Type: Water bottle; Material: Plastic..."
    }
  ],
  "total_results": 1
}
```

**Search Features:**
- **AI-Powered**: Uses CLIP embeddings for semantic matching
- **Multi-modal**: Matches against both image and text descriptions
- **Threshold Filtering**: Only returns results above 0.4 similarity score
- **Weighted Scoring**: 60% text description + 40% image similarity

### Claim an Item

```http
POST /claim
```

**Request Body:**
```json
{
  "filename": "item_12345.jpg",
  "collector_id": 1,
  "verification_details": "This is my water bottle, I lost it yesterday in the library"
}
```

**Response:**
```json
{
  "message": "Item claimed successfully. Please collect within 24 hours.",
  "filename": "item_12345.jpg",
  "collector_id": 1,
  "claim_expiry": "2025-09-21T10:30:00",
  "collection_instructions": "Present your student ID card to collect the item"
}
```

### Collect an Item (Physical Collection)

```http
POST /collect
```

**Content Type:** `multipart/form-data`

**Form Fields:**
- `image`: Current image of the item being collected
- `timestamp`: Collection timestamp
- `box_id`: ID of the collection box
- `collector_id`: ID of the person collecting

**Example:**
```bash
curl -X POST http://localhost:5000/collect \
  -F "image=@backend/uploads/item_12345.jpg" \
  -F "timestamp=$(date +%s)" \
  -F "box_id=box_001" \
  -F "collector_id=1"
```

**Response:**
```json
{
  "message": "Item collected successfully",
  "collection_id": "COL_67890",
  "timestamp": "2025-09-20T14:30:00",
  "box_id": "box_001"
}
```

### Delete an Item

```http
DELETE /delete/{filename}
```

**Example:**
```bash
curl -X DELETE http://localhost:5000/delete/item_12345.jpg
```

**Response:**
```json
{
  "message": "Item deleted successfully",
  "filename": "item_12345.jpg"
}
```

---

## 📦 Box Management APIs

### Register a New Box

```http
POST /box/register
```

**Request Body:**
```json
{
  "box_id": "box_001",
  "capacity": 1,
  "status": "available"
}
```

**Response:**
```json
{
  "message": "Box registered successfully",
  "box_id": "box_001",
  "capacity": 1,
  "status": "available"
}
```

### Get Box Status

```http
GET /box/{box_id}/status
```

**Example:**
```bash
curl http://localhost:5000/box/box_001/status
```

**Response:**
```json
{
  "box_id": "box_001",
  "status": "available",
  "door_status": "closed",
  "capacity": 1,
  "current_load": 0,
  "last_updated": "2025-09-20T10:30:00",
  "is_full": false,
  "should_open": false,
  "door_open": false
}
```

**Box Status Values:**
- `available`: Ready to receive items
- `full`: At capacity (1 item for standard boxes)
- `collect_request`: Full and requesting collection
- `maintenance`: Under maintenance
- `offline`: Not operational

### Update Box Status

```http
POST /box/{box_id}/status
```

**Request Body:**
```json
{
  "status": "full",
  "door_status": "closed", 
  "current_load": 1
}
```

### Open Box Door

```http
POST /box/{box_id}/door/open
```

**Response:**
```json
{
  "message": "Door opened successfully",
  "box_id": "box_001",
  "door_status": "open",
  "instruction": "Box door is now open for item collection"
}
```

### Close Box Door

```http
POST /box/{box_id}/door/close
```

### Request Collection

```http
POST /box/{box_id}/request_collection
```

**Response:**
```json
{
  "message": "Collection requested successfully",
  "box_id": "box_001", 
  "status": "collect_request",
  "door_status": "open",
  "instruction": "Box door is now open for item collection"
}
```

### Mark Collection Complete

```http
POST /box/{box_id}/collection_complete
```

**Response:**
```json
{
  "message": "Collection completed successfully",
  "box_id": "box_001",
  "status": "available",
  "door_status": "closed",
  "current_load": 0
}
```

### Get All Boxes

```http
GET /boxes
```

**Response:**
```json
{
  "boxes": [
    {
      "box_id": "box_001",
      "status": "available",
      "current_load": 0,
      "capacity": 1
    }
  ],
  "total_boxes": 1
}
```

### Get Box Items

```http
GET /box/{box_id}/items
```

**Response:**
```json
{
  "box_id": "box_001",
  "items": [
    {
      "item_id": 42,
      "filename": "item_12345.jpg",
      "upload_date": "2025-09-20T10:30:00"
    }
  ]
}
```

---

## 📊 System Statistics APIs

### Get User Statistics

```http
GET /users/stats
```

**Response:**
```json
{
  "total_finders": 15,
  "total_collectors": 8,
  "active_claims": 3,
  "completed_collections": 42,
  "system_uptime": "5 days, 3 hours"
}
```

---

## 🔧 Error Handling

### Standard Error Response Format

```json
{
  "error": "Description of the error",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common HTTP Status Codes

- **200**: Success
- **400**: Bad Request (invalid data, missing fields)
- **404**: Not Found (item, user, or box not found)
- **500**: Internal Server Error

### Common Error Scenarios

**Image Upload Errors:**
```json
{
  "error": "Lighting is not good enough, please re-upload.",
  "brightness": 0.15,
  "contrast": 0.8
}
```

**Search No Results:**
```json
{
  "message": "Image not found"
}
```

**Box Not Found:**
```json
{
  "error": "Box not found"
}
```

---

## 🛠️ Integration Examples

### Python Integration

```python
import requests

# Upload an item
def upload_item(image_path, description, finder_id):
    url = "http://localhost:5000/upload"
    files = {'image': open(image_path, 'rb')}
    data = {
        'description': description,
        'finder_id': finder_id
    }
    response = requests.post(url, files=files, data=data)
    return response.json()

# Search for items
def search_items(query):
    url = "http://localhost:5000/search"
    data = {'query': query}
    response = requests.post(url, json=data)
    return response.json()

# Example usage
result = upload_item('/path/to/image.jpg', 'Lost water bottle', 1)
search_result = search_items('blue water bottle')
```

### JavaScript/Web Integration

```javascript
// Upload item function
async function uploadItem(imageFile, description, finderId) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('description', description);
    formData.append('finder_id', finderId);

    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}

// Search items function
async function searchItems(query) {
    const response = await fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query })
    });
    
    return await response.json();
}
```

### cURL Testing Examples

```bash
# Test user registration
curl -X POST http://localhost:5000/finder/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@mmu.edu.my","rfid_tag":"TEST123"}'

# Test item search
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"blue water bottle"}'

# Test box status
curl http://localhost:5000/box/box_001/status

# Test collection complete
curl -X POST http://localhost:5000/box/box_001/collection_complete
```

---

## 🚨 Rate Limiting & Best Practices

### API Best Practices

1. **Check Status Codes**: Always check HTTP status codes
2. **Handle Errors Gracefully**: Implement proper error handling
3. **Use Appropriate Content Types**: `application/json` for JSON, `multipart/form-data` for file uploads
4. **Validate Input**: Check data before sending to API
5. **Timeout Handling**: Implement reasonable timeouts for requests

### Performance Considerations

- **Image Size**: Limit uploaded images to reasonable sizes (< 10MB)
- **Batch Operations**: Use bulk operations when possible
- **Caching**: Cache search results when appropriate
- **Connection Pooling**: Reuse HTTP connections for multiple requests

### Security Notes

- **Input Validation**: API performs basic validation, but client-side validation recommended
- **File Safety**: Uploaded files are sanitized with `secure_filename()`
- **RFID Security**: RFID tags should be unique and properly managed
- **Data Privacy**: Handle user data according to privacy requirements

---

## 📚 Related Documentation

- **[Box Guide](box-guide.md)**: Hardware integration and box management
- **[Database Guide](database-guide.md)**: Database schema and management
- **[Testing Guide](testing-guide.md)**: API testing procedures

For more detailed system architecture, see the main `docs/` folder.