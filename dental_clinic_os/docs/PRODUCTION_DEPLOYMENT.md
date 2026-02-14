# Production Deployment Guide for DentalClinicOS

This guide covers production deployment with security hardening, multi-tenant isolation, and scalability considerations.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Security Hardening](#security-hardening)
3. [Database Setup](#database-setup)
4. [Infrastructure Setup](#infrastructure-setup)
5. [Application Configuration](#application-configuration)
6. [Deployment Steps](#deployment-steps)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup Strategy](#backup-strategy)
9. [Scaling Considerations](#scaling-considerations)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Services

- **PostgreSQL 14+**: Primary database with async support
- **Redis 7+**: Caching, sessions, rate limiting
- **MinIO or S3**: Object storage for uploads
- **Nginx**: Reverse proxy and TLS termination
- **Docker & Docker Compose**: Container orchestration

### Security Requirements

- SSL/TLS certificates (Let's Encrypt or commercial)
- Secure SECRET_KEY (32+ characters, randomly generated)
- Stripe API keys (live keys, not test)
- Proper firewall configuration
- Regular security updates

---

## Security Hardening

### 1. Environment Variables

Create a secure `.env` file for production:

```bash
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate-32-char-random-string>
ENCRYPTION_KEY=<generate-fernet-key>

# Database
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/dental_clinic

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Redis
REDIS_URL=redis://:password@redis:6379

# Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=<secure-key>
MINIO_SECRET_KEY=<secure-secret>
MINIO_SECURE=true

# CORS (restrict to your domain)
ALLOWED_ORIGINS=https://your-domain.com

# Rate Limiting
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60

# Monitoring
SENTRY_DSN=https://...
ENABLE_METRICS=true
```

### 2. Generate Secure Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Database Security

```bash
# Create dedicated database user with limited permissions
psql -U postgres

CREATE USER dental_prod WITH PASSWORD 'secure-password';
CREATE DATABASE dental_clinic_prod OWNER dental_prod;
GRANT ALL PRIVILEGES ON DATABASE dental_clinic_prod TO dental_prod;

-- Enable row-level security for tenant isolation
ALTER DATABASE dental_clinic_prod SET default_transaction_isolation = 'read committed';
```

### 4. Nginx Security

Configure Nginx with security headers:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Proxy configuration
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Database Setup

### 1. Run Migrations

```bash
# Activate virtual environment
source backend/.venv/bin/activate

# Run Alembic migrations
cd backend
alembic upgrade head

# Verify tables
psql $DATABASE_URL -c "\dt"
```

### 2. Create Indexes

```sql
-- Performance indexes
CREATE INDEX CONCURRENTLY idx_users_tenant_email ON users(tenant_id, email);
CREATE INDEX CONCURRENTLY idx_assessments_tenant_status ON assessments(tenant_id, status);
CREATE INDEX CONCURRENTLY idx_orders_tenant_status ON orders(tenant_id, status);
CREATE INDEX CONCURRENTLY idx_audit_logs_tenant_created ON audit_logs(tenant_id, created_at DESC);
```

### 3. Row-Level Security (Optional)

Enable RLS for additional tenant isolation:

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_users ON users
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Repeat for other tenant-scoped tables
```

---

## Infrastructure Setup

### 1. Docker Network

```bash
# Create isolated network
docker network create dental-clinic-prod
```

### 2. Docker Compose Production

Use the provided `docker-compose.prod.yml`:

```bash
# Build and start
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check status
docker-compose ps
```

### 3. Resource Limits

Configure resource limits in docker-compose.prod.yml:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## Application Configuration

### 1. Backend Configuration

Edit `backend/app/core/config.py` for production:

```python
class Settings:
    # ... existing config ...
    
    # Production-specific
    if ENVIRONMENT == "production":
        # Force HTTPS
        SECURE_SSL_REDIRECT = True
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
        
        # Rate limiting (stricter)
        RATE_LIMIT_REQUESTS = 60
        RATE_LIMIT_WINDOW = 60
        
        # Token expiration (shorter)
        ACCESS_TOKEN_EXPIRE_MINUTES = 15
        
        # Logging (warnings only)
        LOG_LEVEL = "WARNING"
```

### 2. Frontend Configuration

Set production API URL in `.env`:

```bash
API_BASE_URL=https://your-domain.com/api
```

---

## Deployment Steps

### 1. Pre-Deployment Checklist

- [ ] All environment variables set
- [ ] SSL certificates obtained
- [ ] Database backups created
- [ ] DNS configured
- [ ] Firewall rules set
- [ ] Monitoring configured

### 2. Deploy

```bash
# Pull latest code
git pull origin main

# Build images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Stop old containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Start new containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed initial data (optional)
curl -X POST https://your-domain.com/api/v1/auth/seed-demo-users

# Check logs
docker-compose logs -f
```

### 3. Verify Deployment

```bash
# Health check
curl https://your-domain.com/api/health

# API docs (restricted to internal)
curl https://your-domain.com/api/docs

# Test authentication
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.com","password":"Password123!"}'
```

---

## Monitoring & Logging

### 1. Application Monitoring

Use Sentry for error tracking:

```python
# Already configured in config
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    traces_sample_rate=0.1
)
```

### 2. Metrics

Enable Prometheus metrics:

```bash
# Access metrics
curl http://localhost:8000/metrics
```

### 3. Structured Logging

Logs are already structured using `structlog`:

```python
import structlog
logger = structlog.get_logger()

logger.info("user_logged_in", user_id=str(user.id), tenant_id=str(user.tenant_id))
```

### 4. Log Aggregation

Consider using:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Grafana Loki**
- **CloudWatch** (AWS)

---

## Backup Strategy

### 1. Database Backups

```bash
# Automated daily backup
0 2 * * * pg_dump $DATABASE_URL | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz

# Keep 7 daily, 4 weekly, 3 monthly backups
find /backups -name "db_*.sql.gz" -mtime +7 -delete
```

### 2. Object Storage Backups

Use MinIO versioning or S3 replication:

```yaml
# docker-compose.yml
minio:
  command: server /data --console-address ":9001"
  environment:
    MINIO_VERSIONING_ENABLED: "on"
```

### 3. Restore from Backup

```bash
# Restore database
gunzip < /backups/db_20250214.sql.gz | psql $DATABASE_URL
```

---

## Scaling Considerations

### 1. Horizontal Scaling

```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      replicas: 3  # Run 3 backend instances
```

### 2. Load Balancing

Nginx automatically load balances:

```nginx
upstream backend {
    least_conn;
    server backend:8000;
    server backend:8001;
    server backend:8002;
}
```

### 3. Database Scaling

- **Read replicas**: Use for reporting/analytics queries
- **Connection pooling**: PgBouncer for high concurrency
- **Partitioning**: Partition audit logs by date

### 4. Cache Strategy

```python
# Use Redis for:
- Session storage
- Rate limiting
- Cached queries
- Real-time notifications
```

---

## Troubleshooting

### 1. Database Connection Issues

```bash
# Check database logs
docker-compose logs postgres

# Test connection
psql $DATABASE_URL

# Check connection pool
docker-compose exec backend python -c "from app.db.session import async_engine; print(async_engine.pool.status())"
```

### 2. High Memory Usage

```bash
# Check container stats
docker stats

# Profile memory
docker-compose exec backend python -m memory_profiler app/main.py
```

### 3. Slow Queries

```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### 4. Authentication Issues

```bash
# Check JWT configuration
docker-compose exec backend python -c "from app.core.security import create_access_token; print(create_access_token({'sub': 'test'}, 'test-tenant-id'))"

# Verify token payload
echo <token> | cut -d. -f2 | base64 -d
```

---

## Security Checklist

- [ ] SSL/TLS enabled and configured
- [ ] SECRET_KEY and ENCRYPTION_KEY generated and secured
- [ ] Database credentials strong and rotated regularly
- [ ] Firewall rules restrict unnecessary access
- [ ] Rate limiting enabled
- [ ] Brute force protection active
- [ ] Input validation on all endpoints
- [ ] SQL injection protection (SQLAlchemy)
- [ ] XSS protection headers configured
- [ ] CORS restricted to specific origins
- [ ] Security headers in place (HSTS, CSP, etc.)
- [ ] Regular security updates applied
- [ ] Monitoring and alerting configured
- [ ] Backup strategy implemented and tested
- [ ] Incident response plan documented

---

## Maintenance

### Regular Tasks

- **Daily**: Review logs, check backups
- **Weekly**: Review failed logins, analyze performance
- **Monthly**: Security updates, dependency updates
- **Quarterly**: Full security audit, penetration testing

### Update Procedure

```bash
# 1. Backup
docker-compose exec postgres pg_dump $DATABASE_URL > backup.sql

# 2. Update code
git pull origin main

# 3. Update dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && flutter pub get

# 4. Rebuild and restart
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 5. Verify
curl https://your-domain.com/api/health
```

---

## Support

For issues or questions:
- Documentation: https://docs.dentalclinicos.com
- Email: support@dentalclinicos.com
- GitHub Issues: https://github.com/your-org/dental-clinic-os/issues
