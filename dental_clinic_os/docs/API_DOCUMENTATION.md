# DentalClinicOS API Documentation

## Base URL

```
Development: http://localhost:8000
Production: https://api.dentalclinicos.com
```

## Authentication

All API endpoints (except `/auth/*` and public endpoints) require authentication via JWT bearer token.

```
Authorization: Bearer <access_token>
```

## Response Format

All responses follow this format:

```json
{
  "data": { ... },
  "error": null,
  "success": true
}
```

Error responses:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "success": false
}
```

---

## Authentication Endpoints

### Register User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "role": "patient"
}
```

**Response:** 201 Created
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_at": "2024-01-15T10:30:00Z"
}
```

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:** 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_at": "2024-01-15T10:30:00Z"
}
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:** 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_at": "2024-01-15T11:30:00Z"
}
```

### Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

**Response:** 200 OK
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "patient",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## Products Endpoints

### List Products

```http
GET /api/v1/products/?skip=0&limit=100&active_only=true
Authorization: Bearer <token>
```

**Query Parameters:**
- `skip` (integer): Number of items to skip (default: 0)
- `limit` (integer): Maximum items to return (default: 100, max: 100)
- `active_only` (boolean): Only return active products (default: true)

**Response:** 200 OK
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Cephalometric Analysis",
    "description": "Professional X-ray analysis with AI",
    "price": 299.99,
    "features": [
      "AI-powered landmark detection",
      "Detailed measurements",
      "Treatment recommendations"
    ],
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create Product (Admin Only)

```http
POST /api/v1/products/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "New Service",
  "description": "Service description",
  "price": 199.99,
  "features": ["Feature 1", "Feature 2"]
}
```

---

## Orders Endpoints

### Create Order

```http
POST /api/v1/orders/
Authorization: Bearer <token>
Content-Type: application/json

{
  "items": [
    {
      "product_id": "550e8400-e29b-41d4-a716-446655440001",
      "quantity": 1
    }
  ]
}
```

**Response:** 201 Created
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440002",
  "patient_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_amount": 299.99,
  "status": "pending",
  "invoice_number": "INV-20240101-ABC123",
  "stripe_payment_intent_id": "pi_1234567890",
  "items": [...],
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Confirm Payment

```http
POST /api/v1/orders/{order_id}/pay
Authorization: Bearer <token>
Content-Type: application/json

{
  "payment_method_id": "pm_1234567890"
}
```

**Response:** 200 OK
```json
{
  "order_id": "660e8400-e29b-41d4-a716-446655440002",
  "status": "paid",
  "payment_intent_status": "succeeded"
}
```

### Get My Orders

```http
GET /api/v1/orders/my-orders?skip=0&limit=50
Authorization: Bearer <token>
```

### Refund Order (Admin Only)

```http
POST /api/v1/orders/{order_id}/refund
Authorization: Bearer <token>
Content-Type: application/json

{
  "refund_reason": "Customer request"
}
```

---

## Assessments Endpoints

### Create Assessment

```http
POST /api/v1/assessments/create
Authorization: Bearer <token>
Content-Type: application/json

{
  "order_id": "660e8400-e29b-41d4-a716-446655440002"
}
```

### Upload Image

```http
POST /api/v1/assessments/{assessment_id}/upload-image
Authorization: Bearer <token>
Content-Type: multipart/form-data

image_type: xray
file: <binary file>
```

**Response:** 200 OK
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440003",
  "file_url": "https://storage.dentalclinicos.com/tenant/assessment/20240101/xray.jpg",
  "file_name": "xray.jpg",
  "file_type": "xray",
  "uploaded_at": "2024-01-01T00:00:00Z"
}
```

### Get My Assessments

```http
GET /api/v1/assessments/my-assessments
Authorization: Bearer <token>
```

### Get Pending Assessments (Doctor/Admin)

```http
GET /api/v1/assessments/pending
Authorization: Bearer <token>
```

### Analyze with Manual Measurements (Doctor)

```http
POST /api/v1/assessments/{assessment_id}/analyze
Authorization: Bearer <token>
Content-Type: application/json

{
  "sna": 82.5,
  "snb": 78.3,
  "anb": 4.2,
  "overjet": 5.8,
  "overbite": 3.9
}
```

**Response:** 200 OK
```json
{
  "skeletal_class": "Class II",
  "severity": "Moderate",
  "treatment_suggestion": "Non-extraction with growth modification",
  "confidence_score": 0.85
}
```

### Complete Assessment (Doctor)

```http
POST /api/v1/assessments/{assessment_id}/complete
Authorization: Bearer <token>
Content-Type: application/x-www-form-urlencoded

diagnosis_notes: Treatment plan approved
```

---

## AI Analysis Endpoints

### Analyze X-ray with AI (Doctor)

```http
POST /api/v1/ai/assessments/{assessment_id}/analyze-xray
Authorization: Bearer <token>
```

**Response:** 200 OK
```json
{
  "success": true,
  "assessment_id": "770e8400-e29b-41d4-a716-446655440003",
  "measurements": {
    "SNA": 82.5,
    "SNB": 78.3,
    "ANB": 4.2,
    "Overjet": 5.8,
    "Overbite": 3.9,
    "FMA": 28.5,
    "FMIA": 65.2
  },
  "skeletal_class": "Class II",
  "severity": "Moderate",
  "confidence": 0.87,
  "model_version": "1.0.0",
  "processing_time_ms": 523,
  "findings": [
    "Skeletal pattern identified as Class II",
    "Sella-Nasion-A point angle within normal range"
  ],
  "recommendations": [
    "Functional appliance therapy recommended if growing",
    "Distalization or extraction options available"
  ]
}
```

### Get Model Information

```http
GET /api/v1/ai/models/info
Authorization: Bearer <token>
```

**Response:** 200 OK
```json
{
  "model_version": "1.0.0",
  "model_loaded": true,
  "model_path": "/app/models",
  "supported_image_types": ["xray", "cephalometric", "panoramic"],
  "supported_formats": [".jpg", ".jpeg", ".png", ".dcm", ".dicom"]
}
```

---

## Users Endpoints

### Get My Profile

```http
GET /api/v1/users/me
Authorization: Bearer <token>
```

### Update My Profile

```http
PUT /api/v1/users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "+1987654321",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

### List Users (Doctor/Admin)

```http
GET /api/v1/users/?skip=0&limit=100&role=patient&search=john
Authorization: Bearer <token>
```

**Query Parameters:**
- `skip` (integer): Pagination offset
- `limit` (integer): Items per page
- `role` (enum): Filter by role (patient, doctor, admin)
- `search` (string): Search by name or email

### Create User (Admin)

```http
POST /api/v1/users/
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "SecurePass123!",
  "first_name": "New",
  "last_name": "User",
  "phone": "+1234567890",
  "role": "doctor"
}
```

### Activate/Deactivate User (Admin)

```http
POST /api/v1/users/{user_id}/activate
Authorization: Bearer <token>

POST /api/v1/users/{user_id}/deactivate
Authorization: Bearer <token>
```

---

## Tenants Endpoints (Super Admin Only)

### Create Tenant

```http
POST /api/v1/tenants/
Authorization: Bearer <token> (Super Admin)
Content-Type: application/json

{
  "name": "Dental Clinic ABC",
  "slug": "dental-clinic-abc",
  "domain": "abc.dentalclinicos.com",
  "admin_email": "admin@abc.com",
  "admin_password": "SecurePass123!",
  "admin_first_name": "Admin",
  "admin_last_name": "User",
  "plan": "basic",
  "trial_days": 30
}
```

**Response:** 201 Created
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440004",
  "name": "Dental Clinic ABC",
  "slug": "dental-clinic-abc",
  "domain": "abc.dentalclinicos.com",
  "status": "trial",
  "plan": "basic",
  "max_users": 10,
  "max_storage_gb": 100.0,
  "monthly_revenue": 0.0,
  "trial_ends_at": "2024-02-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Get Tenant Statistics

```http
GET /api/v1/tenants/{tenant_id}/stats
Authorization: Bearer <token>
```

**Response:** 200 OK
```json
{
  "user_count": 25,
  "active_user_count": 20,
  "order_count": 150,
  "monthly_revenue": 15000.00,
  "storage_used_gb": 45.2,
  "storage_limit_gb": 100.0
}
```

### Suspend Tenant

```http
POST /api/v1/tenants/{tenant_id}/suspend
Authorization: Bearer <token>
Content-Type: application/json

{
  "reason": "Non-payment"
}
```

---

## Webhooks

### Stripe Webhook

```http
POST /api/v1/webhooks/stripe/
Content-Type: application/json
Stripe-Signature: t=...

<Stripe webhook payload>
```

**Supported Events:**
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `charge.refunded`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

---

## Error Codes

| Code | Description |
|------|-------------|
| `AUTH_INVALID` | Invalid authentication credentials |
| `AUTH_EXPIRED` | Token has expired |
| `AUTH_LOCKED` | Account locked due to failed attempts |
| `PERMISSION_DENIED` | Insufficient permissions |
| `TENANT_NOT_FOUND` | Tenant not found |
| `TENANT_SUSPENDED` | Tenant account suspended |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `VALIDATION_ERROR` | Request validation failed |
| `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| `PAYMENT_FAILED` | Payment processing failed |
| `UPLOAD_FAILED` | File upload failed |
| `AI_ERROR` | AI analysis failed |

---

## Rate Limiting

- Default: 100 requests per minute per tenant/IP
- Unauthenticated: 30 requests per minute
- Rate limit headers included in response:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

---

## Internationalization

All responses include `Content-Language` header. Support for:
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `zh` - Chinese
- `ar` - Arabic
- `pt` - Portuguese

Example request:
```http
GET /api/v1/products/
Accept-Language: es
```

---

## Tenant Identification

Tenants can be identified via:

1. **Subdomain**: `clinic1.dentalclinicos.com`
2. **Header**: `X-Tenant-ID: tenant-slug or tenant-uuid`
3. **JWT Token**: Tenant ID embedded in token

---

## SDK Examples

### Python

```python
import requests

base_url = "https://api.dentalclinicos.com/api/v1"

# Login
response = requests.post(f"{base_url}/auth/login", json={
    "email": "user@example.com",
    "password": "password123"
})
token = response.json()["access_token"]

# Get products
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{base_url}/products/", headers=headers)
products = response.json()
```

### JavaScript/TypeScript

```typescript
const baseUrl = 'https://api.dentalclinicos.com/api/v1';

// Login
const loginResponse = await fetch(`${baseUrl}/auth/login`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});
const {access_token} = await loginResponse.json();

// Get products
const productsResponse = await fetch(`${baseUrl}/products/`, {
  headers: {'Authorization': `Bearer ${access_token}`}
});
const products = await productsResponse.json();
```

---

## Testing

### Health Check

```http
GET /api/health
```

**Response:** 200 OK
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production"
}
```

### API Documentation

Interactive API documentation available at:
- Swagger UI: `https://api.dentalclinicos.com/api/docs`
- ReDoc: `https://api.dentalclinicos.com/api/redoc`
- OpenAPI JSON: `https://api.dentalclinicos.com/api/openapi.json`

---

## Support

For API support:
- Email: api-support@dentalclinicos.com
- Documentation: https://docs.dentalclinicos.com
- Issues: https://github.com/your-org/dental-clinic-os/issues
