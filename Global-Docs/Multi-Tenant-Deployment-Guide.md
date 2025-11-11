# Multi-Tenant Deployment Guide

**Version:** 1.0  
**Last Updated:** October 20, 2025  
**Status:** Production Ready  

## Overview

This guide provides comprehensive instructions for deploying multiple applications on a single AWS EC2 Ubuntu server using multi-tenant architecture patterns. Based on successful deployments of Functional Fitness USA and Innovation Forge websites, this guide covers server setup, application deployment, and operational management.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Multi-Tenant Architecture](#multi-tenant-architecture)
4. [Application Deployment](#application-deployment)
5. [Database Configuration](#database-configuration)
6. [Email System Setup](#email-system-setup)
7. [SSL/HTTPS Configuration](#sslhttps-configuration)
8. [Process Management](#process-management)
9. [Monitoring & Logging](#monitoring--logging)
10. [Maintenance & Updates](#maintenance--updates)
11. [Troubleshooting](#troubleshooting)
12. [Security Considerations](#security-considerations)

---

## Prerequisites

### Required Tools
- AWS CLI configured with appropriate permissions
- SSH access to EC2 instances
- Domain names with DNS control
- SSL certificates (Let's Encrypt recommended)

### AWS Resources
- EC2 instance (t3.medium or larger recommended)
- Security Groups configured for HTTP/HTTPS/SSH
- Elastic IP (optional but recommended)
- Route 53 hosted zone (for DNS management)

### Local Development
- Node.js 18+ installed
- PostgreSQL client tools
- Git for version control

---

## Server Setup

### 1. Launch EC2 Instance

```bash
# Create EC2 instance using AWS CLI
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Multi-Tenant-Server}]'
```

### 2. Initial Server Configuration

```bash
# Connect to server
ssh -i your-key.pem ubuntu@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git nginx postgresql postgresql-contrib certbot python3-certbot-nginx

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 globally
sudo npm install -g pm2

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### 3. Configure Firewall

```bash
# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

---

## Multi-Tenant Architecture

### Environment Variable Namespacing

Each project must use unique environment variable prefixes to avoid conflicts:

```bash
# Project 1: Functional Fitness USA
FFUSA_DATABASE_URL=postgresql://ffusa_user:password@localhost:5432/ffusa_db
FFUSA_NEXTAUTH_SECRET=secret1
FFUSA_NEXTAUTH_URL=https://functionalfitnessusa.com

# Project 2: Innovation Forge
INNOVATION_DATABASE_URL=postgresql://innovation_user:password@localhost:5432/innovation_db
INNOVATION_NEXTAUTH_SECRET=secret2
INNOVATION_NEXTAUTH_URL=https://tenant2.ai
```

### Port Range Allocation

Assign specific port ranges to each project:

```bash
# Port allocation strategy
Project 1 (FFUSA):     3000-3009 (Web), 4000-4009 (API)
Project 2 (Innovation): 3010-3019 (Web), 4010-4019 (API)
Project 3 (Future):     3020-3029 (Web), 4020-4029 (API)
```

### Directory Structure

```
/opt/apps/
├── ffusa/                    # Functional Fitness USA
│   ├── current/              # Symlink to active version
│   ├── releases/             # Version history
│   │   ├── v1.0.0/
│   │   └── v1.0.1/
│   ├── shared/               # Shared assets
│   └── logs/                 # Application logs
├── innovation/               # Innovation Forge
│   ├── current/
│   ├── releases/
│   ├── shared/
│   └── logs/
└── shared/                   # Global shared resources
    ├── ssl/                  # SSL certificates
    ├── scripts/              # Deployment scripts
    └── configs/              # Nginx configs
```

---

## Application Deployment

### 1. Prepare Application for Deployment

```bash
# In your local project directory
npm run build
npm run test

# Create deployment package
tar -czf app-deployment.tar.gz \
  .next/ \
  public/ \
  package.json \
  package-lock.json \
  next.config.js \
  tailwind.config.js \
  tsconfig.json
```

### 2. Deploy to Server

```bash
# Upload to server
scp -i your-key.pem app-deployment.tar.gz ubuntu@your-server:/tmp/

# On server, extract and setup
ssh -i your-key.pem ubuntu@your-server
cd /opt/apps/your-project/
mkdir -p releases/v1.0.0
cd releases/v1.0.0
tar -xzf /tmp/app-deployment.tar.gz

# Install dependencies
npm ci --production

# Create symlink to current
cd /opt/apps/your-project/
ln -sfn releases/v1.0.0 current
```

### 3. Configure PM2

Create PM2 ecosystem file for each project:

```javascript
// /opt/apps/your-project/ecosystem.config.js
module.exports = {
  apps: [{
    name: 'your-project-web',
    cwd: '/opt/apps/your-project/current',
    script: 'npm',
    args: 'start',
    env: {
      NODE_ENV: 'production',
      PORT: 3000,
      // Add all your namespaced environment variables
    },
    instances: 1,
    exec_mode: 'fork',
    watch: false,
    max_memory_restart: '1G',
    error_file: '/opt/apps/your-project/logs/error.log',
    out_file: '/opt/apps/your-project/logs/out.log',
    log_file: '/opt/apps/your-project/logs/combined.log',
    time: true
  }]
}
```

### 4. Start Application

```bash
# Start with PM2
pm2 start /opt/apps/your-project/ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u ubuntu --hp /home/ubuntu
```

---

## Database Configuration

### 1. Create Project-Specific Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user for each project
CREATE DATABASE your_project_db;
CREATE USER your_project_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE your_project_db TO your_project_user;

# Exit PostgreSQL
\q
```

### 2. Run Database Migrations

```bash
# In your project directory
cd /opt/apps/your-project/current

# Set database URL
export DATABASE_URL="postgresql://your_project_user:secure_password@localhost:5432/your_project_db"

# Run migrations (adjust command based on your setup)
npm run db:migrate
# or
npx prisma migrate deploy
```

### 3. Database Isolation Best Practices

- Each project gets its own database and user
- Use connection pooling to manage resources
- Regular backups with project-specific naming
- Monitor database performance per project

---

## Email System Setup

### 1. AWS SES Configuration

```bash
# Configure AWS SES (if using AWS)
aws ses verify-email-identity --email-address noreply@yourdomain.com
aws ses verify-domain-identity --domain yourdomain.com
```

### 2. Environment Variables for Email

```bash
# Add to your project's environment
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-user
SMTP_PASS=your-ses-smtp-password
FROM_EMAIL=noreply@yourdomain.com
```

### 3. Email Testing

```bash
# Test email functionality
curl -X POST http://localhost:3000/api/test-email \
  -H "Content-Type: application/json" \
  -d '{"to": "test@example.com", "subject": "Test", "body": "Test message"}'
```

---

## SSL/HTTPS Configuration

### 1. Obtain SSL Certificates

```bash
# Using Let's Encrypt
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# For multiple domains
sudo certbot --nginx -d domain1.com -d domain2.com -d domain3.com
```

### 2. Configure Nginx Virtual Hosts

```nginx
# /etc/nginx/sites-available/your-project
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

### 3. Enable Site and Test

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/your-project /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Process Management

### 1. PM2 Configuration

```bash
# View all processes
pm2 list

# Monitor processes
pm2 monit

# Restart specific process
pm2 restart your-project-web

# Stop process
pm2 stop your-project-web

# Delete process
pm2 delete your-project-web
```

### 2. Systemd Integration

```bash
# PM2 automatically creates systemd services
sudo systemctl status pm2-ubuntu

# Enable auto-start
sudo systemctl enable pm2-ubuntu
```

### 3. Process Monitoring

```bash
# Check process health
pm2 show your-project-web

# View logs
pm2 logs your-project-web

# Monitor resource usage
pm2 monit
```

---

## Monitoring & Logging

### 1. Log Directory Structure

```
/opt/apps/
├── ffusa/logs/
│   ├── access.log
│   ├── error.log
│   ├── combined.log
│   └── pm2.log
├── innovation/logs/
│   ├── access.log
│   ├── error.log
│   ├── combined.log
│   └── pm2.log
└── shared/logs/
    ├── nginx/
    │   ├── access.log
    │   └── error.log
    └── system/
        ├── auth.log
        └── syslog
```

### 2. Log Rotation

```bash
# Configure logrotate for PM2 logs
sudo nano /etc/logrotate.d/pm2

# Add configuration
/opt/apps/*/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        pm2 reloadLogs
    endscript
}
```

### 3. Health Monitoring

```bash
# Create health check script
sudo nano /opt/apps/shared/scripts/health-check.sh

#!/bin/bash
# Check if all applications are running
pm2 list | grep -q "online" || exit 1

# Check database connectivity
psql -h localhost -U postgres -c "SELECT 1;" > /dev/null || exit 1

# Check Nginx status
systemctl is-active --quiet nginx || exit 1

echo "All systems healthy"
```

---

## Maintenance & Updates

### 1. Application Updates

```bash
# Create update script
sudo nano /opt/apps/shared/scripts/update-app.sh

#!/bin/bash
PROJECT_NAME=$1
NEW_VERSION=$2

if [ -z "$PROJECT_NAME" ] || [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <project-name> <version>"
    exit 1
fi

cd /opt/apps/$PROJECT_NAME

# Create new release directory
mkdir -p releases/$NEW_VERSION
cd releases/$NEW_VERSION

# Extract new version (assuming tar.gz uploaded)
tar -xzf /tmp/${PROJECT_NAME}-${NEW_VERSION}.tar.gz

# Install dependencies
npm ci --production

# Run database migrations
npm run db:migrate

# Update symlink
cd /opt/apps/$PROJECT_NAME
ln -sfn releases/$NEW_VERSION current

# Restart application
pm2 restart ${PROJECT_NAME}-web

echo "Updated $PROJECT_NAME to version $NEW_VERSION"
```

### 2. Database Backups

```bash
# Create backup script
sudo nano /opt/apps/shared/scripts/backup-databases.sh

#!/bin/bash
BACKUP_DIR="/opt/apps/shared/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup each project database
for db in ffusa_db innovation_db; do
    pg_dump -h localhost -U postgres $db > $BACKUP_DIR/${db}_${DATE}.sql
done

# Compress backups
gzip $BACKUP_DIR/*_${DATE}.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Database backup completed"
```

### 3. Automated Maintenance

```bash
# Create systemd timer for maintenance
sudo nano /etc/systemd/system/app-maintenance.service

[Unit]
Description=Application Maintenance
After=network.target

[Service]
Type=oneshot
ExecStart=/opt/apps/shared/scripts/maintenance.sh
User=ubuntu

# Create timer
sudo nano /etc/systemd/system/app-maintenance.timer

[Unit]
Description=Run application maintenance daily
Requires=app-maintenance.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target

# Enable timer
sudo systemctl enable app-maintenance.timer
sudo systemctl start app-maintenance.timer
```

---

## Troubleshooting

### Common Issues

#### 1. Port Conflicts

```bash
# Check port usage
sudo netstat -tlnp | grep :3000

# Kill process using port
sudo fuser -k 3000/tcp
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connectivity
psql -h localhost -U postgres -c "SELECT version();"

# Check database users
sudo -u postgres psql -c "\du"
```

#### 3. PM2 Process Issues

```bash
# Reset PM2
pm2 kill
pm2 resurrect

# Check PM2 logs
pm2 logs --lines 100

# Restart all processes
pm2 restart all
```

#### 4. Nginx Configuration Issues

```bash
# Test Nginx configuration
sudo nginx -t

# Check Nginx status
sudo systemctl status nginx

# View Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Performance Optimization

#### 1. Database Optimization

```sql
-- Check database performance
SELECT * FROM pg_stat_activity;

-- Analyze table statistics
ANALYZE;

-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

#### 2. Application Optimization

```bash
# Monitor PM2 processes
pm2 monit

# Check memory usage
free -h

# Check disk usage
df -h
```

---

## Security Considerations

### 1. Server Hardening

```bash
# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no

# Use key-based authentication only
# Set: PasswordAuthentication no

# Restart SSH
sudo systemctl restart ssh
```

### 2. Database Security

```bash
# Secure PostgreSQL
sudo nano /etc/postgresql/14/main/postgresql.conf
# Set: listen_addresses = 'localhost'

sudo nano /etc/postgresql/14/main/pg_hba.conf
# Ensure only local connections allowed
```

### 3. Application Security

- Use environment variables for sensitive data
- Implement proper CORS policies
- Use HTTPS everywhere
- Regular security updates
- Monitor for suspicious activity

### 4. Backup Security

```bash
# Encrypt backups
gpg --symmetric --cipher-algo AES256 backup.sql

# Store backups securely
aws s3 cp backup.sql.gpg s3://your-backup-bucket/
```

---

## Quick Reference

### Essential Commands

```bash
# Deploy new version
./update-app.sh project-name v1.0.1

# Check system health
./health-check.sh

# Backup databases
./backup-databases.sh

# View logs
pm2 logs project-name-web

# Restart service
pm2 restart project-name-web

# Check Nginx status
sudo systemctl status nginx

# Test SSL certificate
sudo certbot certificates
```

### Port Allocation

| Project | Web Port | API Port | Database |
|---------|----------|----------|----------|
| FFUSA | 3000 | 4000 | ffusa_db |
| Innovation | 3010 | 4010 | innovation_db |
| Future 1 | 3020 | 4020 | future1_db |
| Future 2 | 3030 | 4030 | future2_db |

### Environment Variable Template

```bash
# Project-specific prefix
PROJECT_DATABASE_URL=postgresql://user:pass@localhost:5432/db
PROJECT_NEXTAUTH_SECRET=your-secret
PROJECT_NEXTAUTH_URL=https://yourdomain.com
PROJECT_SMTP_HOST=smtp.yourprovider.com
PROJECT_SMTP_USER=your-smtp-user
PROJECT_SMTP_PASS=your-smtp-password
```

---

## Conclusion

This multi-tenant deployment guide provides a comprehensive framework for deploying multiple applications on a single server. The architecture ensures proper isolation, security, and maintainability while optimizing resource usage.

### Key Success Factors

1. **Proper Namespacing**: Environment variables and resources must be properly namespaced
2. **Port Management**: Systematic port allocation prevents conflicts
3. **Database Isolation**: Each project gets its own database and user
4. **Process Management**: PM2 provides reliable process management
5. **Monitoring**: Comprehensive logging and health monitoring
6. **Security**: Proper SSL, firewall, and access controls
7. **Backup Strategy**: Regular, automated backups with retention policies

### Next Steps

1. Implement monitoring and alerting
2. Set up automated deployment pipelines
3. Add performance monitoring and optimization
4. Implement disaster recovery procedures
5. Regular security audits and updates

---

**Last Updated:** October 20, 2025  
**Maintained By:** AI Development Team  
**Status:** Production Ready ✅
