# Multi-Tenant Server Deployment
**Running Multiple Applications on a Single Ubuntu Server**

## Overview

Multi-tenant deployment involves hosting multiple independent applications on a single server. This guide covers the architecture, configuration, and best practices for deploying multiple Next.js/Node.js applications with isolated databases, separate PM2 processes, and individual Nginx configurations.

**Created:** October 19, 2025  
**Server:** Ubuntu 20.04+ (AWS EC2)  
**Example:** Running Functional Fitness USA + Innovation Forge on `98.89.40.81`

---

## Architecture

```
                    ┌─────────────────────────┐
                    │   Internet (Port 443)   │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │    Nginx (Port 80/443)  │
                    │    SSL/TLS Termination  │
                    └───────────┬─────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
    ┌───────▼──────┐    ┌───────▼──────┐   ┌───────▼──────┐
    │   tenant1    │    │   tenant2    │   │   tenant3    │
    │   .ai:443    │    │   .ai:443     │   │   .com:443   │
    └───────┬──────┘    └───────┬───────┘   └───────┬──────┘
            │                   │                    │
    ┌───────▼──────┐    ┌───────▼───────┐   ┌───────▼──────┐
    │ PM2 Process  │    │  PM2 Process  │   │ PM2 Process  │
    │ Port: 3010   │    │  Port: 3000   │   │ Port: 3020   │
    └───────┬──────┘    └───────┬───────┘   └───────┬──────┘
            │                   │                    │
    ┌───────▼──────┐    ┌───────▼───────┐   ┌───────▼──────┐
    │  PostgreSQL  │    │  PostgreSQL   │   │  PostgreSQL  │
    │ DB: fitness  │    │ DB: innovation│   │ DB: project3 │
    └──────────────┘    └───────────────┘   └──────────────┘
```

---

## Directory Structure

```
/var/www/
├── functional-fitness-usa/
│   ├── .next/
│   ├── .env (project-specific)
│   ├── package.json
│   ├── pm2.config.js
│   └── ...
│
├── innovation-forge-website/
│   ├── .next/
│   ├── .env (project-specific)
│   ├── package.json
│   ├── pm2.config.js
│   └── ...
│
└── project-three/
    ├── .next/
    ├── .env (project-specific)
    ├── package.json
    └── ...

/etc/nginx/sites-available/
├── tenant1.ai
├── tenant2.ai
└── tenant3.com

/var/log/
├── functional-fitness/
│   └── *.log
├── innovation-forge/
│   └── *.log
└── project3/
    └── *.log
```

---

## Port Allocation Strategy

### System Ports

- **80:** HTTP (Nginx)
- **443:** HTTPS (Nginx)
- **5432:** PostgreSQL
- **22:** SSH

### Application Ports (Internal)

Assign non-overlapping port ranges per project:

| Project | Port Range | Current Use |
|---------|------------|-------------|
| Project 1 | 3000-3010 | 3010 (API/Web) |
| Project 2 | 3011-3020 | 3000 (API/Web) |
| Project 3 | 3021-3030 | TBD |
| Project 4 | 3031-3040 | TBD |

**Convention:**
- Main application: First port in range (e.g., 3000)
- API server (if separate): +1 (e.g., 3001)
- Additional services: +2, +3, etc.

---

## Step-by-Step Deployment

### 1. Upload Application

```bash
# From local machine
scp -i key.pem source.tar.gz ubuntu@server-ip:/var/www/

# On server
cd /var/www
sudo mkdir -p project-name
sudo tar -xzf source.tar.gz -C project-name
sudo chown -R ubuntu:ubuntu project-name
cd project-name
```

### 2. Install Dependencies

```bash
npm ci --omit=dev
```

**OR for development mode:**
```bash
npm install
```

### 3. Configure Environment

**Create `/var/www/project-name/.env`:**
```env
# Environment
NODE_ENV=production

# Server
PORT=3000
NEXT_PUBLIC_BASE_URL=https://your-domain.com

# Database
DATABASE_URL=postgresql://project_user:password@localhost:5432/project_db

# Email
AWS_SES_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
AWS_SES_SMTP_PORT=587
AWS_SES_SMTP_USER=your_smtp_user
AWS_SES_SMTP_PASSWORD=your_smtp_password
EMAIL_FROM=noreply@your-domain.com
EMAIL_TO=info@your-domain.com
EMAIL_MODE=production

# AI APIs
EXA_API_KEY=your_key
OPENAI_API_KEY=your_key
GEMINI_API_KEY=your_key
PERPLEXITY_API_KEY=your_key
```

**Set permissions:**
```bash
chmod 600 .env
```

### 4. Setup Database

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE project_db;
CREATE USER project_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE project_db TO project_user;
\c project_db
GRANT ALL ON SCHEMA public TO project_user;
EOF

# Load migrations
psql -h localhost -U project_user -d project_db -f migrations/001_init.sql
psql -h localhost -U project_user -d project_db -f migrations/002_tables.sql
```

### 5. Start with PM2

**Create `pm2.config.js`:**
```javascript
module.exports = {
  apps: [{
    name: 'project-name',
    script: 'node_modules/next/dist/bin/next',
    args: 'start',
    env: {
      NODE_ENV: 'production',
      PORT: 3000,
    },
    instances: 1,
    exec_mode: 'cluster',
    watch: false,
    max_memory_restart: '1G',
    error_file: '/var/log/project-name/error.log',
    out_file: '/var/log/project-name/output.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
  }],
};
```

**Start application:**
```bash
# Create log directory
sudo mkdir -p /var/log/project-name
sudo chown ubuntu:ubuntu /var/log/project-name

# Start with PM2
pm2 start pm2.config.js
pm2 save
pm2 startup
```

### 6. Configure Nginx

**Create `/etc/nginx/sites-available/your-domain.com`:**
```nginx
# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS - Main application
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/your-domain.access.log;
    error_log /var/log/nginx/your-domain.error.log;

    # Proxy to application
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/your-domain.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Setup SSL

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 8. Verify Deployment

```bash
# Check PM2 status
pm2 list

# Check application logs
pm2 logs project-name --lines 50

# Check Nginx
sudo systemctl status nginx

# Test application
curl -I https://your-domain.com
```

---

## Environment Variable Management

### Problem: Variable Conflicts

**Issue:** Global `/etc/environment` variables override project-specific `.env` files

**Example Conflict:**
```bash
# /etc/environment (GLOBAL - affects all projects)
SMTP_HOST=localhost
SMTP_PORT=25

# /var/www/project-a/.env (PROJECT - should win but doesn't)
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
```

**Result:** Project A tries to use `localhost:25` instead of AWS SES!

### Solution: Variable Namespacing

**Global Variables (Use AWS-specific prefix):**
```bash
# /etc/environment
AWS_SES_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
AWS_SES_SMTP_PORT=587
```

**Project Variables:**
```env
# Project A .env
AWS_SES_SMTP_USER=project_a_user
AWS_SES_SMTP_PASSWORD=project_a_password
EMAIL_FROM=noreply@projecta.com
EMAIL_TO=info@projecta.com

# Project B .env
AWS_SES_SMTP_USER=project_b_user
AWS_SES_SMTP_PASSWORD=project_b_password
EMAIL_FROM=noreply@projectb.com
EMAIL_TO=info@projectb.com
```

**Application Code (Priority order):**
```typescript
const smtpHost = 
  process.env.AWS_SES_SMTP_HOST ||  // Project-specific AWS
  process.env.SMTP_HOST ||           // Fallback
  'localhost';                       // Default
```

### Best Practices

1. **Global vars:** Infrastructure only (AWS region, general settings)
2. **Project vars:** Credentials, API keys, project-specific settings
3. **Use prefixes:** `AWS_`, `PROJECT_NAME_`, etc.
4. **Never duplicate:** Same variable name in global + project = conflict
5. **Document clearly:** Which vars are global vs project-specific

---

## Database Isolation

### Separate Databases per Project

```sql
-- Create isolated database and user for each project
CREATE DATABASE project1_db;
CREATE USER project1_user WITH PASSWORD 'strong_password_1';
GRANT ALL PRIVILEGES ON DATABASE project1_db TO project1_user;

CREATE DATABASE project2_db;
CREATE USER project2_user WITH PASSWORD 'strong_password_2';
GRANT ALL PRIVILEGES ON DATABASE project2_db TO project2_user;

-- Grant schema permissions
\c project1_db
GRANT ALL ON SCHEMA public TO project1_user;

\c project2_db
GRANT ALL ON SCHEMA public TO project2_user;
```

### Database Access Restrictions

**Edit `/etc/postgresql/14/main/pg_hba.conf`:**
```conf
# Each project user can only access their database
local   project1_db     project1_user                   md5
local   project2_db     project2_user                   md5

# Deny cross-project access
local   project1_db     project2_user                   reject
local   project2_db     project1_user                   reject
```

**Reload PostgreSQL:**
```bash
sudo systemctl reload postgresql
```

---

## PM2 Management

### List All Applications

```bash
pm2 list
```

**Output:**
```
┌────┬───────────────────────────┬─────────┬─────────┬──────────┬────────┬──────┐
│ id │ name                      │ mode    │ pid     │ uptime   │ status │ cpu  │
├────┼───────────────────────────┼─────────┼─────────┼──────────┼────────┼──────┤
│ 0  │ functional-fitness-usa    │ fork    │ 275636  │ 4D       │ online │ 0%   │
│ 4  │ innovation-forge          │ fork    │ 323184  │ 5h       │ online │ 0%   │
└────┴───────────────────────────┴─────────┴─────────┴──────────┴────────┴──────┘
```

### Restart Specific Application

```bash
# Restart with env reload
pm2 reload project-name --update-env

# Or delete and restart
pm2 delete project-name
pm2 start pm2.config.js
```

### View Logs

```bash
# Live logs for one app
pm2 logs project-name --lines 100

# All apps
pm2 logs --lines 50

# Error logs only
pm2 logs project-name --err --lines 50
```

### Resource Monitoring

```bash
# Real-time monitoring
pm2 monit

# Memory/CPU stats
pm2 status
```

---

## Security Considerations

### 1. File Permissions

```bash
# Application files
sudo chown -R ubuntu:ubuntu /var/www/project-name
chmod 755 /var/www/project-name
chmod 644 /var/www/project-name/.env  # or 600 for secrets

# Log files
sudo chown -R ubuntu:ubuntu /var/log/project-name
chmod 755 /var/log/project-name
```

### 2. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Block application ports from external access
# (Nginx reverse proxy handles routing)
```

### 3. Database Security

```bash
# Restrict PostgreSQL to localhost only
# /etc/postgresql/14/main/postgresql.conf
listen_addresses = 'localhost'

# Require passwords
# /etc/postgresql/14/main/pg_hba.conf
local   all             all                             md5
host    all             all             127.0.0.1/32    md5
```

### 4. Environment File Security

```bash
# Secure .env files
chmod 600 /var/www/project-name/.env

# Add to .gitignore
echo ".env" >> .gitignore

# Never commit sensitive data
git status  # Verify .env not tracked
```

### 5. SSL/TLS

```bash
# Auto-renewal for Let's Encrypt
sudo certbot renew --dry-run

# Check certificate expiry
sudo certbot certificates

# Set up auto-renewal cron
sudo crontab -e
# Add: 0 0 * * * certbot renew --quiet
```

---

## Monitoring & Alerts

### Server Health

```bash
# Disk usage
df -h

# Memory usage
free -h

# CPU usage
top

# All processes
htop
```

### Application Health Checks

**Create health endpoint:**
```typescript
// app/api/healthz/route.ts
export async function GET() {
  return Response.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
}
```

**Monitor with script:**
```bash
#!/bin/bash
DOMAINS=("tenant1.ai" "tenant2.ai")

for domain in "${DOMAINS[@]}"; do
  status=$(curl -s -o /dev/null -w "%{http_code}" https://$domain/api/healthz)
  if [ $status -eq 200 ]; then
    echo "✓ $domain: healthy"
  else
    echo "✗ $domain: unhealthy (status: $status)"
  fi
done
```

### Log Rotation

**Create `/etc/logrotate.d/project-name`:**
```
/var/log/project-name/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 ubuntu ubuntu
    sharedscripts
    postrotate
        pm2 reloadLogs
    endscript
}
```

---

## Backup Strategy

### Database Backups

```bash
#!/bin/bash
# /usr/local/bin/backup-databases.sh

BACKUP_DIR="/var/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup each database
pg_dump -h localhost -U project1_user project1_db | gzip > $BACKUP_DIR/project1_$DATE.sql.gz
pg_dump -h localhost -U project2_user project2_db | gzip > $BACKUP_DIR/project2_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backups completed: $DATE"
```

**Schedule with cron:**
```bash
sudo crontab -e
# Daily at 2 AM
0 2 * * * /usr/local/bin/backup-databases.sh >> /var/log/backups.log 2>&1
```

### Application Backups

```bash
# Backup application files (excluding node_modules, .next)
tar -czf /var/backups/project-name-$(date +%Y%m%d).tar.gz \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='.git' \
  /var/www/project-name

# Upload to S3 (optional)
aws s3 cp /var/backups/project-name-$(date +%Y%m%d).tar.gz \
  s3://your-backup-bucket/project-name/
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
sudo lsof -i :3000

# Kill process
kill -9 <PID>

# Or use PM2
pm2 delete project-name
```

### Nginx Configuration Errors

```bash
# Test configuration
sudo nginx -t

# View error log
sudo tail -f /var/log/nginx/error.log

# Reload (if test passed)
sudo systemctl reload nginx
```

### PM2 Process Crashes

```bash
# View error logs
pm2 logs project-name --err --lines 100

# Check for common issues:
# - Missing environment variables
# - Database connection failure
# - Port conflicts
# - Out of memory

# Restart with more memory
pm2 delete project-name
pm2 start pm2.config.js --max-memory-restart 2G
```

### Database Connection Issues

```bash
# Test connection
psql -h localhost -U project_user -d project_db -c "SELECT 1;"

# Check PostgreSQL status
sudo systemctl status postgresql

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

---

## Performance Optimization

### 1. Enable Gzip Compression

**Nginx configuration:**
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
```

### 2. Enable HTTP/2

**Already enabled in example:**
```nginx
listen 443 ssl http2;
```

### 3. PM2 Cluster Mode

**For CPU-intensive apps:**
```javascript
module.exports = {
  apps: [{
    instances: 'max',  // Use all CPU cores
    exec_mode: 'cluster',
  }],
};
```

### 4. Database Connection Pooling

```typescript
import { Pool } from 'pg';

const pool = new Pool({
  host: 'localhost',
  user: 'project_user',
  password: process.env.DB_PASSWORD,
  database: 'project_db',
  max: 20,  // Maximum connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

---

## Scaling Considerations

### Vertical Scaling (Single Server)

1. Upgrade EC2 instance type
2. Increase memory allocation per PM2 process
3. Add more PM2 instances (cluster mode)
4. Optimize database queries
5. Add Redis caching

### Horizontal Scaling (Multiple Servers)

1. Load balancer (AWS ALB/NLB)
2. Managed database (AWS RDS)
3. Shared file storage (AWS EFS)
4. Session management (Redis)
5. CDN for static assets (CloudFront)

---

## Related Documentation

- [AWS-SES-EMAIL-INTEGRATION.md](./AWS-SES-EMAIL-INTEGRATION.md) - Email system for multi-tenant
- [SYSTEMD-DAEMON-SETUP.md](./SYSTEMD-DAEMON-SETUP.md) - Automated tasks per project
- [AI-COLLABORATIVE-AUTHORING-SYSTEM.md](./AI-COLLABORATIVE-AUTHORING-SYSTEM.md) - Example system deployed

---

**Last Updated:** October 19, 2025  
**Maintained By:** AI Development Team

