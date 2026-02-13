# DentalClinicOS API Documentation

## Base URL
```
Development: http://localhost:8000/api/v1
Production: https://api.dentalclinicos.com/api/v1
```

## Authentication

All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Authentication Endpoints

#### Register User
```http
POST /auth/register
```

Request body:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "role": "patient"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2024-02-13T15:30:00Z"
}
```

#### Login
```http
POST /auth/login
```

Request body:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Response: Same as register

#### Refresh Token
```http
POST /auth/refresh
```

Request body:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "role": "patient",
  "is_active": true,
  "avatar_url": null,
  "created_at": "2024-02-13T10:00:00Z",
  "updated_at": "2024-02-13T10:00:00Z"
}
```

---

## Assessment Engine

### Create Assessment
```http
POST /assessments/create
Authorization: Bearer <token>
```

Request body:
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

### Upload Image
```http
POST /assessments/{assessment_id}/upload-image?image_type=xray
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

Form data:
- `file`: Image file (JPG, PNG, DICOM)
- `image_type`: xray, intraoral, or cephalometric

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "file_url": "https://storage.dentalclinic.com/...",
  "file_name": "xray_001.jpg",
  "file_type": "xray",
  "uploaded_at": "2024-02-13T10:30:00Z"
}
```

### Analyze Assessment
```http
POST /assessments/{assessment_id}/analyze
Authorization: Bearer <token>
```

Request body:
```json
{
  "sna": 82,
  "snb": 78,
  "anb": 4,
  "overjet": 6,
  "overbite": 4
}
```

Response:
```json
{
  "skeletal_class": "Class II",
  "severity": "Moderate",
  "treatment_suggestion": "Non-extraction with growth modification if patient is growing. Consider functional appliances or headgear.",
  "confidence_score": 0.85
}
```

### Get My Assessments (Patient)
```http
GET /assessments/my-assessments
Authorization: Bearer <token>
```

Response:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "order_id": "550e8400-e29b-41d4-a716-446655440001",
    "patient_id": "550e8400-e29b-41d4-a716-446655440000",
    "doctor_id": null,
    "status": "pending_upload",
    "measurements": null,
    "skeletal_class": null,
    "severity": null,
    "treatment_suggestion": null,
    "confidence_score": null,
    "created_at": "2024-02-13T10:00:00Z",
    "updated_at": "2024-02-13T10:00:00Z"
  }
]
```

### Get Pending Assessments (Doctor)
```http
GET /assessments/pending
Authorization: Bearer <token>
```

### Complete Assessment
```http
POST /assessments/{assessment_id}/complete
Authorization: Bearer <token>
```

Request body:
```json
{
  "diagnosis_notes": "Patient shows moderate Class II skeletal pattern..."
}
```

### Generate Report
```http
GET /assessments/{assessment_id}/report
Authorization: Bearer <token>
```

Response:
```json
{
  "message": "Report generation endpoint",
  "assessment_id": "550e8400-e29b-41d4-a716-446655440002",
  "download_url": "/api/v1/assessments/.../download-report"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error",
  "errors": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions. Doctor access required."
}
```

### 404 Not Found
```json
{
  "detail": "Assessment not found"
}
```

---

## Rate Limiting

API requests are limited to:
- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

---

## WebSocket Support (Future)

Real-time notifications will be available via WebSocket:
```
ws://localhost:8000/ws/notifications
```

---

## API Versioning

Current version: **v1**

Version is included in the URL path:
```
/api/v1/...
```

Future versions will be accessible via:
```
/api/v2/...
```