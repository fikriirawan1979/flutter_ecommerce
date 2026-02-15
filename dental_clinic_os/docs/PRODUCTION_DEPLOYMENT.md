# Production Deployment Guide

## Overview

This guide covers deploying DentalClinicOS to production with security hardening, monitoring, and multi-tenancy.

## Prerequisites

- Docker and Docker Compose installed
- Domain name configured (e.g., `app.dentalclinicos.com`)
- SSL certificates (Let's Encrypt recommended)
- Production database server (PostgreSQL 15+)
- Redis server (or cloud Redis)
- Object storage (MinIO or S3-compatible)
- Stripe account with live keys
- SMTP server for emails (SendGrid, AWS SES, etc.)
- Monitoring solution (Sentry recommended)

## Architecture

```
┌─────────────┐
│   Nginx     │ (SSL termination, reverse proxy)
└──────┬──────┘
       │
       ├──────────────┬──────────────┬─────────────┐
       │              │              │             │
┌──────▼──────┐ ┌────▼────┐ ┌─────▼────┐ ┌─────▼────┐
│  Backend    │ │ Frontend│ │  MinIO   │ │  Redis   │
│  (FastAPI)  │ │(Flutter)│ │          │ │          │
└──────┬──────┘ └─────────┘ └──────────┘ └──────────┘
       │
┌──────▼──────┐
│ PostgreSQL  │
└─────────────┘
```

## Deployment Steps

### 1. Prepare Environment Variables

```bash
cd dental_clinic_os
cp .env.production .env
```

Edit `.env` with production values:

```bash
nano .env
```

**Critical security settings:**

```bash
# Generate strong secrets
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Set in .env
echo "SECRET_KEY=$SECRET_KEY" >> .env
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env
```

### 2. Configure SSL Certificates

#### Option A: Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d app.dentalclinicos.com -d api.dentalclinicos.com

# Certificate location: /etc/letsencrypt/live/app.dentalclinicos.com/
```

#### Option B: Custom Certificates

Place certificates in `docker/nginx/ssl/`:

```bash
mkdir -p docker/nginx/ssl
cp /path/to/fullchain.pem docker/nginx/ssl/
cp /path/to/privkey.pem docker/nginx/ssl/
chmod 600 docker/nginx/ssl/*
```

### 3. Configure Nginx

Edit `docker/nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name app.dentalclinicos.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Tenant-ID $http_x_tenant_id;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # MinIO (if needed)
    location /storage/ {
        proxy_pass http://minio:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name app.dentalclinicos.com;
    return 301 https://$server_name$request_uri;
}
```

### 4. Production Docker Compose

```bash
# Build and start production containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 5. Database Initialization

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# Create default tenant
curl -X POST https://api.dentalclinicos.com/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Default Clinic",
    "slug": "default-clinic",
    "admin_email": "admin@dentalclinicos.com",
    "admin_password": "STRONG_PASSWORD_HERE",
    "admin_first_name": "Admin",
    "admin_last_name": "User"
  }'
```

### 6. Configure Stripe Webhooks

1. Log in to Stripe Dashboard
2. Go to Developers → Webhooks
3. Add endpoint: `https://api.dentalclinicos.com/api/v1/webhooks/stripe/`
4. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.refunded`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy webhook secret and add to `.env`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

### 7. Setup Monitoring

#### Sentry (Error Tracking)

```bash
# Install Sentry SDK
pip install sentry-sdk

# Configure in backend/app/core/config.py
SENTRY_DSN=https://YOUR_DSN@sentry.io/PROJECT_ID
```

#### Prometheus (Metrics)

```bash
# Prometheus is already configured in requirements.txt
# Enable metrics in .env:
ENABLE_METRICS=true

# Metrics endpoint: http://localhost:8000/metrics
```

#### Health Checks

```bash
# Health check endpoint
curl https://api.dentalclinicos.com/api/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production"
}
```

## Security Hardening Checklist

### Backend Security

- [ ] Strong SECRET_KEY (32+ characters)
- [ ] Strong ENCRYPTION_KEY (Fernet)
- [ ] HTTPS only (SSL/TLS)
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] CORS restricted to production domains
- [ ] Database connection using SSL
- [ ] MinIO using secure connection
- [ ] Webhook signature verification enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection protection (SQLAlchemy)
- [ ] XSS protection
- [ ] CSRF protection for state-changing operations

### Database Security

- [ ] Strong database password
- [ ] Restricted database user permissions
- [ ] Regular database backups
- [ ] Encryption at rest (if supported)
- [ ] SSL connections only
- [ ] Network isolation (VPC)

### Infrastructure Security

- [ ] Firewall rules configured
- [ ] SSH key-based authentication
- [ ] Regular security updates
- [ ] Log aggregation and monitoring
- [ ] Intrusion detection (optional)

## Monitoring and Alerts

### Key Metrics to Monitor

- **Application**: Response time, error rate, request rate
- **Database**: Connection pool, query performance, disk usage
- **Redis**: Memory usage, hit rate, connections
- **MinIO**: Storage usage, request rate
- **System**: CPU, memory, disk, network

### Alerting Setup

Configure alerts for:
- Error rate > 5%
- Response time > 2s (P95)
- Database connection pool exhausted
- Disk usage > 80%
- High memory usage
- Failed login attempts spike

## Backup Strategy

### Database Backups

```bash
# Daily automated backups (via cron)
0 2 * * * /usr/bin/docker-compose exec -T postgres pg_dump -U dental_user dental_clinic | gzip > /backup/dental_clinic_$(date +\%Y\%m\%d).sql.gz

# Keep 30 days of daily backups
find /backup -name "dental_clinic_*.sql.gz" -mtime +30 -delete
```

### File Storage Backups

MinIO provides built-in replication or use external backup solution.

## Scaling Considerations

### Horizontal Scaling

- **Backend**: Deploy multiple instances behind Nginx load balancer
- **Frontend**: Deploy to CDN (Vercel, Netlify, or S3)
- **Database**: Use read replicas for read-heavy workloads
- **Redis**: Use Redis Cluster for distributed caching

### Vertical Scaling

- Increase CPU/memory for compute-intensive tasks (AI analysis)
- Use dedicated GPU servers for ML inference

## Disaster Recovery

### Recovery Plan

1. **Immediate Actions**:
   - Identify affected services
   - Switch to backup if needed
   - Notify stakeholders

2. **Database Recovery**:
   ```bash
   # Restore from backup
   gunzip < /backup/dental_clinic_20240101.sql.gz | docker-compose exec -T postgres psql -U dental_user dental_clinic
   ```

3. **Application Recovery**:
   - Redeploy from CI/CD
   - Restore environment variables
   - Verify health checks

## Performance Optimization

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX CONCURRENTLY idx_assessments_tenant_status ON assessments(tenant_id, status);
CREATE INDEX CONCURRENTLY idx_orders_tenant_status ON orders(tenant_id, status);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM assessments WHERE tenant_id = '...';
```

### Caching Strategy

- Cache frequently accessed data (products, user info)
- Cache API responses with short TTL
- Use Redis for session storage

## Maintenance

### Regular Tasks

- **Daily**: Check error logs, system health
- **Weekly**: Review security updates, backup verification
- **Monthly**: Database maintenance, performance review
- **Quarterly**: Security audit, capacity planning

### Log Rotation

```bash
# Configure logrotate for application logs
/var/log/dental_clinic_os/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        docker-compose restart backend
    endscript
}
```

## Troubleshooting

### Common Issues

**1. Database connection failed**
```bash
# Check database status
docker-compose ps postgres
docker-compose logs postgres

# Verify connection string
echo $DATABASE_URL
```

**2. MinIO upload failed**
```bash
# Check MinIO status
docker-compose ps minio
docker-compose logs minio

# Verify credentials
echo $MINIO_ACCESS_KEY
echo $MINIO_SECRET_KEY
```

**3. High memory usage**
```bash
# Check container resource usage
docker stats

# Restart services
docker-compose restart backend
```

## Support

For production issues:
- Check logs: `docker-compose logs -f`
- Review metrics: Prometheus/Grafana dashboards
- Error tracking: Sentry
- Documentation: [GitHub Wiki](https://github.com/your-org/dental-clinic-os/wiki)

## Compliance

### HIPAA Compliance (if applicable)

- Data encryption at rest and in transit
- Audit logging for all PHI access
- Access controls and authentication
- Business Associate Agreements (BAAs) with vendors
- Regular security assessments
- Incident response procedures

### GDPR Compliance (if applicable)

- Data minimization
- Right to erasure
- Data portability
- Consent management
- Data breach notification
