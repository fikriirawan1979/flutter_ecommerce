# Deployment Guide

## Table of Contents
1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Environment Variables](#environment-variables)
5. [Database Migrations](#database-migrations)
6. [Monitoring & Logging](#monitoring--logging)

---

## Local Development Setup

### Prerequisites
- Docker & Docker Compose
- Flutter SDK (for frontend development)
- Python 3.11+ (for backend development)

### Quick Start

1. **Clone the repository**:
```bash
git clone https://github.com/your-org/dental-clinic-os.git
cd dental-clinic-os
```

2. **Create environment file**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start services with Docker**:
```bash
docker-compose up -d
```

4. **Access the application**:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/api/docs
- MinIO Console: http://localhost:9001

### Backend Development (without Docker)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
flutter pub get
flutter run -d chrome  # or -d windows, -d macos
```

---

## Docker Deployment

### Build Images

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend
```

### Run Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: data loss)
docker-compose down -v
```

### Health Checks

```bash
# Check backend health
curl http://localhost:8000/api/health

# Check database
 docker-compose exec postgres pg_isready -U dental_user

# Check all services
docker-compose ps
```

---

## Production Deployment

### Server Requirements
- Ubuntu 20.04 LTS or higher
- 4GB RAM minimum (8GB recommended)
- 50GB disk space
- Docker & Docker Compose installed

### Deployment Steps

1. **Prepare server**:
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Setup application**:
```bash
mkdir -p /opt/dental-clinic-os
cd /opt/dental-clinic-os
# Copy docker-compose.yml and .env
```

3. **Configure SSL (Let's Encrypt)**:
```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to nginx ssl folder
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/nginx/ssl/
```

4. **Update docker-compose for production**:
```yaml
# Add to docker-compose.yml
services:
  backend:
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
```

5. **Deploy**:
```bash
docker-compose pull
docker-compose up -d
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@db:5432/dbname` |
| `SECRET_KEY` | JWT secret key | `your-super-secret-key` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `https://yourdomain.com` |
| `MINIO_ENDPOINT` | Object storage endpoint | `minio:9000` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT token expiry |

---

## Database Migrations

### Using Alembic

```bash
# Initialize migrations (first time only)
docker-compose exec backend alembic init migrations

# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Run migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

### Manual Database Setup

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U dental_user -d dental_clinic

# Run seed data
docker-compose exec backend python -c "from app.db.seed import seed_data; seed_data()"
```

---

## Monitoring & Logging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Health Monitoring

The application exposes health endpoints:
- Backend: `GET /api/health`
- Database: Built-in PostgreSQL health checks

### Prometheus Metrics (Optional)

Enable Prometheus metrics by setting:
```env
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Backup Strategy

```bash
# Database backup
docker-compose exec postgres pg_dump -U dental_user dental_clinic > backup.sql

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U dental_user dental_clinic | gzip > "backups/db_$DATE.sql.gz"
```

---

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 80, 443, 5432, 6379, 8000, 9000 are available
2. **Permission denied**: Run `sudo chown -R $USER:$USER /opt/dental-clinic-os`
3. **Database connection failed**: Check DATABASE_URL and network connectivity
4. **Memory issues**: Increase Docker memory limit to 4GB+

### Support

For issues and support:
- GitHub Issues: https://github.com/your-org/dental-clinic-os/issues
- Documentation: https://docs.dentalclinicos.com
- Email: support@dentalclinicos.com