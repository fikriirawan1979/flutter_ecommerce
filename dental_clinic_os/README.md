# DentalClinicOS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flutter](https://img.shields.io/badge/Flutter-3.0+-blue.svg)](https://flutter.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)

A comprehensive, production-ready macOS-style Dental Assessment Clinic Management System built with Flutter and FastAPI.

## 🎯 Project Overview

DentalClinicOS is an enterprise-grade end-to-end dental clinic management system featuring:

### ✨ Core Features
- **Multi-role Authentication** (Patient/Doctor/Admin/Super Admin) with JWT
- **Multi-Tenancy** with complete data and storage isolation
- **E-commerce Module** with Stripe payment integration
- **AI-Powered X-Ray Analysis** with automatic landmark detection
- **Rule-based Assessment Engine** for cephalometric analysis
- **File Upload System** with MinIO/S3 integration
- **Internationalization** support for 7 languages
- **PDF Report Generation** with WeasyPrint
- **Real-time Dashboards** with comprehensive analytics
- **Audit Logging** for compliance and security

### 🔒 Security & Compliance
- **Enterprise Security**: TLS/SSL, encryption at rest, rate limiting
- **HIPAA-Ready**: Comprehensive audit logging, access controls
- **GDPR-Compliant**: Data privacy controls, right to erasure
- **Multi-factor Authentication** (MFA) ready
- **Webhook Signature Verification** for payments

## 🏗️ Architecture

### Clean Architecture (DDD)

```
dental_clinic_os/
├── frontend/              # Flutter Application
│   ├── lib/
│   │   ├── core/         # Theme, constants, utilities
│   │   ├── features/     # Feature modules (Auth, E-commerce, Assessment)
│   │   ├── shared/       # Shared widgets and utilities
│   │   └── routes/       # GoRouter configuration
│   └── ...
│
├── backend/              # FastAPI Application
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Security, config
│   │   ├── db/           # Database models & session
│   │   ├── models/       # SQLAlchemy models
│   │   └── schemas/      # Pydantic schemas
│   ├── assessment_engine/# Rule-based diagnostic engine
│   └── ...
│
├── docker/               # Docker configurations
├── docs/                 # Documentation
└── .github/              # CI/CD workflows
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Flutter SDK 3.0+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Docker Deployment (Recommended)

```bash
# Clone repository
git clone https://github.com/your-org/dental-clinic-os.git
cd dental_clinic_os

# Copy environment template
cp .env.example .env
nano .env  # Edit with your settings

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# Seed demo data
curl -X POST http://localhost:8000/api/v1/auth/seed-demo-users
```

**Access Points:**
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs (Swagger UI)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Frontend**: http://localhost:3000

**Demo Credentials:**
- **Patient**: patient@demo.com / password123
- **Doctor**: doctor@demo.com / password123
- **Admin**: admin@demo.com / password123

### Local Development

See [QUICK_START.md](docs/QUICK_START.md) for detailed development setup.

## 🛠️ Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
flutter pub get
flutter run -d chrome  # or -d windows, -d macos
```

### Database Migrations
```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Run migrations
docker-compose exec backend alembic upgrade head
```

## 📊 Features

### Authentication & Authorization
- **JWT Authentication**: Access and refresh tokens with automatic rotation
- **Role-Based Access Control**: Patient, Doctor, Admin, Super Admin roles
- **Multi-Factor Authentication**: Ready for TOTP implementation
- **Password Security**: Bcrypt hashing (12 rounds), strength validation, expiration tracking
- **Account Security**: Lockout after 5 failed attempts, brute force protection

### Multi-Tenancy
- **Tenant Isolation**: Complete data separation at database and storage levels
- **Tenant Identification**: Subdomain, header, or JWT-based
- **Tenant Management**: Create, update, suspend, activate tenants
- **Storage Isolation**: Separate MinIO buckets per tenant
- **Status Management**: Active, Suspended, Trial, Cancelled statuses

### AI-Powered X-Ray Analysis
- **Automatic Landmark Detection**: 15+ cephalometric points detected by AI
- **Measurement Extraction**: Automatic calculation of all key measurements
- **Skeletal Classification**: Class I/II/III with severity assessment
- **Treatment Recommendations**: AI-generated treatment suggestions
- **Confidence Scoring**: Model confidence metrics
- **Manual Analysis**: Option for doctor to manually enter measurements

Example AI analysis output:
```json
{
  "success": true,
  "measurements": {
    "SNA": 82.5,
    "SNB": 78.3,
    "ANB": 4.2,
    "Overjet": 5.8,
    "Overbite": 3.9
  },
  "skeletal_class": "Class II",
  "severity": "Moderate",
  "confidence": 0.87,
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

### E-commerce Module
- **Product Catalog**: Manage assessment packages and services
- **Shopping Cart**: Add items to cart, calculate totals
- **Stripe Integration**: Secure payment processing with Payment Intents
- **Order Management**: Track orders through payment to completion
- **Refund Processing**: Handle refunds with Stripe integration
- **Invoice Generation**: Automatic invoice creation and PDF generation
- **Dashboard Statistics**: Revenue, orders, assessments metrics

### File Upload & Storage
- **MinIO Integration**: Secure object storage with S3-compatible API
- **File Validation**: Size, type, and MIME type validation
- **Checksum Verification**: SHA-256 checksums for integrity
- **Tenant Isolation**: Separate storage paths per tenant
- **Multiple Image Types**: X-ray, intraoral, cephalometric, panoramic
- **Presigned URLs**: Secure temporary access URLs

### Internationalization
- **7 Languages**: English, Spanish, French, German, Chinese, Arabic, Portuguese
- **Automatic Detection**: Locale detection from Accept-Language header
- **Comprehensive Translations**: All user-facing messages translated
- **RTL Support**: Right-to-left layout for Arabic
- **Fallback**: Automatic fallback to English for unsupported languages

### Dashboard Features
- **Patient Dashboard**: Active orders, upload images, track status, view reports
- **Doctor Dashboard**: Pending reviews, AI analysis tools, annotation, report generation
- **Admin Dashboard**: User management, analytics, revenue tracking, tenant management

## 🎨 UI/UX Design

### macOS Human Interface Guidelines
- Glassmorphism effects
- Sidebar navigation (Finder-style)
- Rounded corners (12-16px)
- SF Pro typography
- 8pt spacing grid
- Soft neutral color palette

### Design System
```dart
// Colors
AppColors.primary       // #007AFF
AppColors.success       // #34C759
AppColors.warning       // #FF9500
AppColors.error         // #FF3B30

// Typography
AppTypography.heading1  // 48px, Bold
AppTypography.heading2  // 36px, Bold
AppTypography.bodyLarge // 17px, Regular

// Spacing
AppSpacing.xs           // 4px
AppSpacing.sm           // 8px
AppSpacing.md           // 16px
AppSpacing.lg           // 24px
```

## 🔒 Security

- JWT token authentication
- Password hashing with bcrypt
- Role-based access control (RBAC)
- CORS configuration
- Input validation
- SQL injection protection (SQLAlchemy)
- XSS protection

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests
```bash
cd frontend
flutter test --coverage
```

## 🚢 Deployment

### Production Checklist
- [ ] Update `.env` with production values
- [ ] Configure SSL certificates
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure backups
- [ ] Enable rate limiting
- [ ] Set up logging aggregation

### Docker Production
```bash
# Production build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

## 📈 CI/CD

GitHub Actions workflow includes:
- Automated testing
- Code coverage reporting
- Docker image building
- Deployment to production

## 📚 Documentation

- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete API reference with examples
- **[Quick Start Guide](docs/QUICK_START.md)** - Get started in 5 minutes
- **[Production Deployment](docs/PRODUCTION_DEPLOYMENT.md)** - Production deployment guide
- **[Security Audit](docs/SECURITY_AUDIT.md)** - Security review and recommendations
- **[Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md)** - Feature implementation details
- **[Changelog](CHANGELOG.md)** - Version history and changes

## 🔒 Security

DentalClinicOS follows security best practices:

- **Authentication**: JWT with refresh tokens, role-based access control
- **Encryption**: TLS/SSL for transit, Fernet for data at rest
- **Isolation**: Multi-tenant data and storage isolation
- **Rate Limiting**: Per-tenant/IP rate limiting
- **Audit Logging**: Comprehensive logging of all actions
- **Input Validation**: Pydantic validation on all inputs
- **SQL Injection**: Protected by SQLAlchemy ORM
- **XSS Protection**: Content security headers and sanitization

See [SECURITY_AUDIT.md](docs/SECURITY_AUDIT.md) for complete security details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- Flutter Team for the amazing framework
- FastAPI for high-performance Python API
- PostgreSQL for reliable data storage
- MinIO for object storage

## 📞 Support

- Issues: [GitHub Issues](https://github.com/your-org/dental-clinic-os/issues)
- Email: support@dentalclinicos.com
- Documentation: https://docs.dentalclinicos.com

---

Built with ❤️ for better dental healthcare