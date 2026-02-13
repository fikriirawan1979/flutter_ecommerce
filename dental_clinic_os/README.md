# DentalClinicOS

A comprehensive macOS-style Dental Assessment Clinic Application built with Flutter and FastAPI.

## 🎯 Project Overview

DentalClinicOS is an end-to-end clinic management system featuring:
- **Multi-role Authentication** (Patient/Doctor/Admin)
- **E-commerce Module** for assessment packages
- **File Upload System** for dental images (X-ray, intraoral)
- **Rule-based Assessment Engine** for cephalometric analysis
- **PDF Report Generation**
- **Real-time Dashboards** with analytics

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
- Flutter SDK 3.0+
- Python 3.11+

### 1. Clone Repository
```bash
git clone https://github.com/your-org/dental-clinic-os.git
cd dental_clinic_os
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 3. Run with Docker
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access Application
- **Web App**: http://localhost:3000
- **API Documentation**: http://localhost:8000/api/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

### 5. Seed Demo Data
```bash
# Create demo users
curl -X POST http://localhost:8000/api/v1/auth/seed-demo-users
```

Demo credentials:
- **Patient**: patient@demo.com / password123
- **Doctor**: doctor@demo.com / password123
- **Admin**: admin@demo.com / password123

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

### Authentication System
- JWT-based authentication
- Role-based access control
- Secure password hashing (bcrypt)
- Token refresh mechanism

### E-commerce Module
- Product catalog with categories
- Shopping cart functionality
- Order management
- Payment status simulation
- Invoice generation

### Assessment Engine
- Cephalometric measurement input
- Rule-based diagnostic classification
- AI-ready architecture for future ML integration
- Confidence scoring
- Structured JSON output

Example assessment input:
```json
{
  "SNA": 82,
  "SNB": 78,
  "ANB": 4,
  "Overjet": 6,
  "Overbite": 4
}
```

Example output:
```json
{
  "skeletal_class": "Class II",
  "severity": "Moderate",
  "treatment_suggestion": "Non-extraction with growth modification",
  "confidence_score": 0.85
}
```

### Dashboard Features
- **Patient Dashboard**: Active orders, upload images, track status
- **Doctor Dashboard**: Pending reviews, annotation tools, report generation
- **Admin Dashboard**: User management, analytics, revenue tracking

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

- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Architecture Decisions](docs/ARCHITECTURE.md)
- [Contributing Guidelines](CONTRIBUTING.md)

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