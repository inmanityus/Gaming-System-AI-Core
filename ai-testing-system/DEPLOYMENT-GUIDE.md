# 🚀 Validation Report System - Deployment Guide

## Quick Start

### Option 1: Local Development

```bash
# Backend
cd ai-testing-system/orchestrator
pip install -r requirements.txt
python database/init_db.py
python main.py  # Runs on http://localhost:8000

# Frontend
cd ai-testing-system/dashboard
npm install
npm run dev  # Runs on http://localhost:3000
```

### Option 2: Docker Production (Recommended)

```bash
# Build Docker image with GTK for PDF support
docker build -t qa-orchestrator:latest -f Dockerfile .
docker run -p 8000:8000 --env-file .env qa-orchestrator:latest
```

---

## 📋 Prerequisites

### Required Services

1. **PostgreSQL 13+**
   - Database: `body_broker_qa`
   - Port: 5443 (or configure in .env)
   - User: `postgres` with password

2. **AWS S3**
   - Bucket: `body-broker-qa-reports`
   - Region: `us-east-1`
   - IAM permissions: s3:PutObject, s3:GetObject, s3:DeleteObject

3. **System Libraries** (Linux only, for PDF)
   - libpango-1.0-0
   - libpangocairo-1.0-0
   - libgdk-pixbuf2.0-0
   - shared-mime-info

### Environment Variables

Create `.env` file in `ai-testing-system/orchestrator/`:

```env
# Database
DB_HOST=localhost
DB_PORT=5443
DB_NAME=body_broker_qa
DB_USER=postgres
DB_PASSWORD=your_password_here

# S3 Storage
S3_BUCKET_REPORTS=body-broker-qa-reports
S3_BUCKET_CAPTURES=body-broker-qa-captures
S3_REGION=us-east-1

# AWS Credentials (or use IAM roles)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Rate Limiting
RATE_LIMIT_REPORTS_PER_MINUTE=10

# Cache Configuration
CACHE_MAX_SIZE=1000
CACHE_TTL_HOURS=24

# PDF Generation
PDF_MAX_WORKERS=2
PDF_GENERATION_TIMEOUT=120
```

Create `.env.local` in `ai-testing-system/dashboard/`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=development
```

---

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install GTK libraries for WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p templates/reports sample_reports

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health').raise_for_status()"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  qa-orchestrator:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=body_broker_qa
      - DB_USER=postgres
      - DB_PASSWORD=${DB_PASSWORD}
      - S3_BUCKET_REPORTS=body-broker-qa-reports
      - S3_REGION=us-east-1
    depends_on:
      - postgres
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=body_broker_qa
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    ports:
      - "5443:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## 🔧 Production Deployment (AWS EC2)

### Step 1: Prepare AWS Resources

```bash
# Create S3 bucket
aws s3 mb s3://body-broker-qa-reports --region us-east-1

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket body-broker-qa-reports \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket body-broker-qa-reports \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable versioning (optional)
aws s3api put-bucket-versioning \
  --bucket body-broker-qa-reports \
  --versioning-configuration Status=Enabled
```

### Step 2: Deploy to EC2

```bash
# SSH into EC2 instance
ssh ubuntu@54.174.89.122

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker (if not installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clone/copy code
git clone <your-repo> /home/ubuntu/qa-orchestrator
# OR
scp -r ai-testing-system/orchestrator/* ubuntu@54.174.89.122:~/qa-orchestrator/

# Navigate to directory
cd /home/ubuntu/qa-orchestrator

# Create .env file
nano .env
# (Paste environment variables from above)

# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f qa-orchestrator

# Verify running
curl http://localhost:8000/health
```

### Step 3: Initialize Database

```bash
# If database doesn't exist
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE body_broker_qa;"

# Run schema initialization
docker-compose exec qa-orchestrator python database/init_db.py
```

### Step 4: Configure Nginx (Optional)

```nginx
server {
    listen 80;
    server_name qa.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Increase timeout for report generation
    proxy_read_timeout 300;
    proxy_connect_timeout 75;
}
```

---

## 🧪 Testing After Deployment

### 1. Health Check

```bash
curl http://your-server:8000/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "s3": "healthy"
  }
}
```

### 2. Generate Test Report

```bash
curl -X POST http://your-server:8000/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "test_run_id": "test_001",
    "format": "html",
    "include_screenshots": true
  }'

# Expected response:
{
  "report_id": "rep_abc123",
  "status": "queued",
  "message": "Report generation started"
}
```

### 3. Check Report Status

```bash
curl http://your-server:8000/reports/rep_abc123

# Poll until status is "completed"
```

### 4. Download Report

```bash
curl http://your-server:8000/reports/rep_abc123/download

# Returns:
{
  "download_url": "https://s3.amazonaws.com/..."
}
```

### 5. Verify Frontend

```
Open browser: http://your-frontend-url/reports
- Should see list of reports
- Click on report to see details
- Download should work
```

---

## 🔍 Troubleshooting

### PDF Generation Fails

**Problem**: `OSError: cannot load library 'libgobject-2.0-0'`

**Solution**: 
- Linux: Install GTK libraries (see Prerequisites)
- Windows: Use Docker with Linux base image
- Production: Always use Docker

### Database Connection Fails

**Problem**: `connection refused` or `database does not exist`

**Solution**:
```bash
# Create database
psql -h localhost -p 5443 -U postgres -c "CREATE DATABASE body_broker_qa;"

# Run schema
python database/init_db.py

# Check PostgreSQL is running
sudo systemctl status postgresql
```

### S3 Upload Fails

**Problem**: `AccessDenied` or `NoSuchBucket`

**Solution**:
```bash
# Verify bucket exists
aws s3 ls s3://body-broker-qa-reports

# Check IAM permissions
aws s3api get-bucket-policy --bucket body-broker-qa-reports
```

### Rate Limiting Issues

**Problem**: Getting 429 even with low traffic

**Solution**:
- Check if behind proxy: Configure trusted headers
- Increase limit in .env: `RATE_LIMIT_REPORTS_PER_MINUTE=20`
- Use user-based limiting instead of IP

---

## 📊 Monitoring

### Essential Metrics to Watch

1. **API Health**
   - Response time (p95 < 2s)
   - Error rate (< 1%)
   - Rate limit hits

2. **Report Generation**
   - Queue depth
   - Success/failure rate
   - Generation time (p95 < 10s)

3. **Database**
   - Connection pool utilization
   - Query performance
   - Disk usage

4. **S3**
   - Upload success rate
   - Download bandwidth
   - Storage costs

### Prometheus Queries

```promql
# Error rate
rate(report_generation_total{status="failed"}[5m])

# Generation time
histogram_quantile(0.95, rate(report_generation_duration_seconds_bucket[5m]))

# Active reports
active_reports

# Database query latency
histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))
```

---

## 🆘 Support

### Logs Location

- Application: `docker-compose logs qa-orchestrator`
- Database: `docker-compose logs postgres`
- Nginx: `/var/log/nginx/error.log`

### Common Commands

```bash
# Restart services
docker-compose restart

# View real-time logs
docker-compose logs -f

# Check database
docker-compose exec postgres psql -U postgres -d body_broker_qa

# Clear cache
# (Currently in-memory, restarts automatically clear it)

# Manual cleanup old reports
docker-compose exec postgres psql -U postgres -d body_broker_qa \
  -c "SELECT cleanup_old_reports(30);"  # 30 days retention
```

---

## 📚 Additional Resources

- **API Documentation**: http://your-server:8000/docs (FastAPI auto-generated)
- **Metrics**: http://your-server:8000/metrics (Prometheus format)
- **Health**: http://your-server:8000/health
- **Sample Reports**: `ai-testing-system/orchestrator/sample_reports/`

---

**Last Updated**: November 12, 2025  
**Version**: 1.0.0  
**Status**: Production-Ready (Conditional)

