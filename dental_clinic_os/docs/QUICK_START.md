# Quick Start Guide

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

## Quick Start (Docker)

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/dental-clinic-os.git
cd dental_clinic_os

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Initialize Database

```bash
# Seed demo users
curl -X POST http://localhost:8000/api/v1/auth/seed-demo-users

# Response
{
  "message": "Demo users created",
  "tenant_id": "...",
  "users": [
    "patient@demo.com",
    "doctor@demo.com",
    "admin@demo.com"
  ]
}
```

### 4. Access Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Frontend**: http://localhost:3000

### 5. Test Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@demo.com",
    "password": "password123"
  }'
```

## Development Setup

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up pre-commit hooks
pre-commit install

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
flutter pub get

# Run web version
flutter run -d chrome

# Or run desktop version
flutter run -d windows  # Windows
flutter run -d macos    # macOS
flutter run -d linux    # Linux
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

### Frontend Tests

```bash
cd frontend

# Run all tests
flutter test

# Run with coverage
flutter test --coverage

# View coverage report
open coverage/lcov-report/index.html  # macOS
```

## Common Tasks

### Create New API Endpoint

1. Create endpoint file in `backend/app/api/v1/endpoints/`
2. Add router to `backend/app/main.py`
3. Update API documentation

### Add New Database Model

1. Add model to `backend/app/models/models.py`
2. Add schema to `backend/app/schemas/schemas.py`
3. Create migration: `alembic revision --autogenerate -m "description"`
4. Apply migration: `alembic upgrade head`

### Add New Frontend Screen

1. Create screen file in `frontend/lib/features/*/presentation/screens/`
2. Add route to `frontend/lib/routes/app_router.dart`
3. Add navigation link in menu

## Troubleshooting

### Database Connection Failed

```bash
# Check database status
docker-compose ps postgres
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Rebuild and start
docker-compose up -d --build postgres
```

### MinIO Upload Failed

```bash
# Check MinIO status
docker-compose ps minio
docker-compose logs minio

# Verify credentials
echo $MINIO_ACCESS_KEY
echo $MINIO_SECRET_KEY

# Access MinIO console
open http://localhost:9001
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### Cannot Connect to API from Frontend

1. Check CORS settings in `.env`:
   ```bash
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:64298
   ```

2. Verify API is running:
   ```bash
   curl http://localhost:8000/api/health
   ```

3. Check browser console for CORS errors

## Environment Variables

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db

# JWT
SECRET_KEY=your-secret-key-min-32-chars
ENCRYPTION_KEY=your-encryption-key

# Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Monitoring
SENTRY_DSN=https://...
ENABLE_METRICS=true
```

## Production Deployment

See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for detailed production deployment instructions.

## Documentation

- [API Documentation](API_DOCUMENTATION.md) - Complete API reference
- [Production Deployment](PRODUCTION_DEPLOYMENT.md) - Production setup guide
- [Security Audit](SECURITY_AUDIT.md) - Security review and recommendations
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md) - Feature implementation details

## Support

- **Issues**: https://github.com/your-org/dental-clinic-os/issues
- **Documentation**: https://docs.dentalclinicos.com
- **Email**: support@dentalclinicos.com

## License

MIT License - see LICENSE file for details.
