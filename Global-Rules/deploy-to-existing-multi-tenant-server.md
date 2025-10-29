# Deploy to Existing Multi-Tenant Web Server

**Purpose**: Add a new website to an existing AWS EC2 server that's already hosting other sites, safely reusing shared resources without interfering with existing deployments.

**Critical**: This guide includes discovery steps to identify what's already on the server before deploying.

**Alternative**: If setting up a new standalone server, see `deploy-new-standalone-linux-server.md`

---

## Overview

This guide safely adds a new site to an existing multi-tenant server by:
1. **Discovering** what's already deployed (ports, databases, sites)
2. **Planning** deployment to avoid conflicts
3. **Reusing** shared resources (PostgreSQL server, AWS SES, global variables)
4. **Deploying** with proper isolation (own port, database, PM2 process, Nginx config)

**Estimated Time**: 1-2 hours

**Cost**: $0 additional (shared server resources)

---

## Phase 1: Discovery - What's On The Server (15 minutes)

### 1.1 Connect to Server
```bash
# You should have:
# - Server IP (e.g., 98.89.40.81)
# - SSH key file
ssh -i /path/to/key.pem ubuntu@SERVER_IP
```

### 1.2 Check Running PM2 Processes
```bash
pm2 list

# Take note of:
# - Process names (existing sites)
# - Ports being used (look at logs or configs)
# - Memory usage
```

### 1.3 Check Nginx Sites
```bash
ls -la /etc/nginx/sites-enabled/

# For each site, check port number:
grep "proxy_pass" /etc/nginx/sites-enabled/* | grep localhost

# Example output:
# /etc/nginx/sites-enabled/site1.com:    proxy_pass http://localhost:3000;
# /etc/nginx/sites-enabled/site2.com:    proxy_pass http://localhost:3001;
```

**Record Used Ports**: ________________

### 1.4 Check Existing Databases
```bash
sudo -u postgres psql -c "\l"

# Take note of existing database names
# Pattern usually: projectname_website or similar
```

**Record Existing Databases**: ________________

### 1.5 Check Global Environment Variables
```bash
cat /etc/environment

# Check for:
# - NODE_ENV
# - PGPASSWORD (PostgreSQL password)
# - AWS_SES credentials
# - SMTP settings
```

**Record Global Variables**: ________________

### 1.6 Check Available Resources
```bash
# CPU and Memory
htop  # Press q to quit

# Disk space
df -h

# Current load
uptime
```

### 1.7 Check PostgreSQL Version and Settings
```bash
sudo -u postgres psql -c "SELECT version();"

# Check if trust authentication is configured
sudo cat /etc/postgresql/*/main/pg_hba.conf | grep "127.0.0.1"
# Should see: host    all    all    127.0.0.1/32    trust
```

---

## Phase 2: Deployment Planning (10 minutes)

Based on discovery, plan your deployment:

### 2.1 Assign Port Number
**Rule**: Use next available port after highest existing port

Example:
- If existing ports are 3000, 3001
- **Your port**: 3002

**Your Assigned Port**: ________________

### 2.2 Plan Database Name
**Rule**: Use project name with underscores, check for uniqueness

Example: `innovation_forge_website`

**Your Database Name**: ________________

### 2.3 Plan Database User
**Rule**: Similar to database name but with `_user` or short form

Example: `innforge_user`

**Your Database User**: ________________

### 2.4 Plan PM2 Process Name
**Rule**: Short, descriptive, unique

Example: `innovation-forge`

**Your Process Name**: ________________

### 2.5 Verify No Conflicts
```bash
# Check port not in use
sudo netstat -tlnp | grep :YOUR_PORT
# Should return nothing

# Check PM2 process name available
pm2 list | grep "YOUR_PROCESS_NAME"
# Should return nothing

# Check database name available
sudo -u postgres psql -c "\l" | grep "YOUR_DATABASE_NAME"
# Should return nothing
```

---

## Phase 3: Create Database (10 minutes)

### 3.1 Create Database and User
```bash
sudo -u postgres psql

CREATE DATABASE YOUR_DATABASE_NAME;
CREATE USER YOUR_DB_USER WITH PASSWORD 'SECURE_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE YOUR_DATABASE_NAME TO YOUR_DB_USER;
\q
```

### 3.2 Test Connection (Uses PGPASSWORD from /etc/environment)
```bash
psql -h localhost -U YOUR_DB_USER -d YOUR_DATABASE_NAME -c "SELECT version();"
```

### 3.3 Load Schema
```bash
# Upload your schema files first
cd /home/ubuntu
scp -i key.pem migrations/*.sql ubuntu@SERVER_IP:~/

# Then load
psql -h localhost -U YOUR_DB_USER -d YOUR_DATABASE_NAME -f ~/001_initial.sql
psql -h localhost -U YOUR_DB_USER -d YOUR_DATABASE_NAME -f ~/002_data.sql
# etc.
```

---

## Phase 4: Deploy Application Code (20 minutes)

### 4.1 Create Application Directory
```bash
sudo mkdir -p /var/www/YOUR_PROJECT_NAME
sudo chown ubuntu:ubuntu /var/www/YOUR_PROJECT_NAME
```

### 4.2 Upload Code
**From local machine:**
```bash
cd /path/to/your/project
tar -czf app.tar.gz --exclude=node_modules --exclude=.next --exclude=.git \
  --exclude=.env.local --exclude=*.pem .
scp -i key.pem app.tar.gz ubuntu@SERVER_IP:~/
```

**On server:**
```bash
cd /var/www/YOUR_PROJECT_NAME
tar -xzf ~/app.tar.gz
rm ~/app.tar.gz
```

### 4.3 Create Project .env.local
```bash
cd /var/www/YOUR_PROJECT_NAME
nano .env.local

# Add project-specific variables:
DATABASE_URL=postgresql://YOUR_DB_USER:SECURE_PASSWORD@localhost:5432/YOUR_DATABASE_NAME
NEXT_PUBLIC_BASE_URL=https://yourdomain.com
SMTP_FROM_EMAIL=noreply@yourdomain.com
DEFAULT_EMAIL=info@yourdomain.com

# Global variables are inherited from /etc/environment:
# - NODE_ENV=production
# - PGPASSWORD=...
# - AWS_SES credentials (if using)
# - SMTP_HOST, SMTP_PORT
```

### 4.4 Install Dependencies and Build
```bash
cd /var/www/YOUR_PROJECT_NAME
npm install --production
npm run build
```

---

## Phase 5: Start Application with PM2 (10 minutes)

### 5.1 Start Process on Assigned Port
```bash
cd /var/www/YOUR_PROJECT_NAME
pm2 start npm --name "YOUR_PROCESS_NAME" -- start -- -p YOUR_PORT

# Example:
# pm2 start npm --name "innovation-forge" -- start -- -p 3002
```

### 5.2 Save PM2 Configuration
```bash
pm2 save
pm2 list  # Verify your process is running
```

### 5.3 Check Logs
```bash
pm2 logs YOUR_PROCESS_NAME

# Look for:
# - "ready on port YOUR_PORT"
# - Database connection successful
# - No errors
```

---

## Phase 6: Configure Nginx (15 minutes)

### 6.1 Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/yourdomain.com
```

```nginx
# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS - Main application
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL certificates (will be configured by certbot)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
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
    access_log /var/log/nginx/YOUR_PROJECT_NAME.access.log;
    error_log /var/log/nginx/YOUR_PROJECT_NAME.error.log;
    
    # Proxy to application
    location / {
        proxy_pass http://localhost:YOUR_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6.2 Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/yourdomain.com /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

---

## Phase 7: Setup SSL Certificate (10 minutes)

### 7.1 Configure DNS First
**Before running certbot:**
- Add A record: `yourdomain.com` → `SERVER_IP`
- Add A record: `www.yourdomain.com` → `SERVER_IP`
- Wait 5-10 minutes for DNS propagation

### 7.2 Verify DNS
```bash
dig yourdomain.com +short
# Should show SERVER_IP
```

### 7.3 Install SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Certbot will:
# - Verify domain ownership
# - Install certificates
# - Update Nginx configuration
# - Setup auto-renewal
```

### 7.4 Test HTTPS
```bash
curl -I https://yourdomain.com
# Should show: HTTP/2 200
```

---

## Phase 8: Verification (10 minutes)

### 8.1 Test Application
- Visit https://yourdomain.com
- Test all pages
- Test forms
- Check database operations

### 8.2 Verify No Impact on Other Sites
```bash
# Check all PM2 processes still running
pm2 list

# Check other sites still accessible
curl -I https://existing-site1.com
curl -I https://existing-site2.com
```

### 8.3 Check System Resources
```bash
# Memory usage
free -h

# CPU load
uptime

# Disk space
df -h

# All should be healthy
```

### 8.4 Review Logs
```bash
# Your application
pm2 logs YOUR_PROCESS_NAME --lines 50

# Nginx
sudo tail -f /var/log/nginx/YOUR_PROJECT_NAME.access.log
sudo tail -f /var/log/nginx/YOUR_PROJECT_NAME.error.log

# PostgreSQL (if any issues)
sudo tail -f /var/log/postgresql/postgresql-*.log
```

---

## Deployment Summary

After successful deployment, document:

### Your Deployment:
- **Project Name**: ________________
- **Domain**: ________________
- **Server IP**: ________________
- **Port**: ________________
- **Database**: ________________
- **PM2 Process**: ________________
- **Deployed**: [DATE]

### Shared Resources Used:
- PostgreSQL server (existing)
- Global PGPASSWORD (existing)
- AWS SES credentials (existing, if configured)
- Postfix SMTP (existing)

### DNS Configuration for User:
```
A Record: yourdomain.com → SERVER_IP
A Record: www.yourdomain.com → SERVER_IP
```

---

## Common Issues and Solutions

### Port Already in Use
```bash
# Check what's using the port
sudo netstat -tlnp | grep :YOUR_PORT

# If occupied, choose next available port
# Then update PM2 and Nginx configs
```

### PM2 Process Crashes
```bash
pm2 logs YOUR_PROCESS_NAME

# Common issues:
# - Missing environment variables
# - Database connection failed
# - Port conflict

# Fix and restart:
pm2 restart YOUR_PROCESS_NAME
```

### Nginx 502 Bad Gateway
```bash
# Application not running or wrong port
pm2 status
pm2 restart YOUR_PROCESS_NAME

# Check Nginx config has correct port
sudo cat /etc/nginx/sites-available/yourdomain.com | grep proxy_pass
```

### Database Connection Failed
```bash
# Verify database exists
sudo -u postgres psql -c "\l" | grep YOUR_DATABASE_NAME

# Test connection
psql -h localhost -U YOUR_DB_USER -d YOUR_DATABASE_NAME -c "SELECT 1;"

# Check /etc/environment has PGPASSWORD
cat /etc/environment | grep PGPASSWORD
```

### SSL Certificate Fails
```bash
# Check DNS is configured correctly
dig yourdomain.com +short

# Check port 80 accessible (certbot needs it)
sudo netstat -tlnp | grep :80

# Try again
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## Maintenance

### Update Application
```bash
cd /var/www/YOUR_PROJECT_NAME
git pull  # or upload new code
npm install
npm run build
pm2 restart YOUR_PROCESS_NAME
```

### Database Migrations
```bash
cd /var/www/YOUR_PROJECT_NAME
psql -h localhost -U YOUR_DB_USER -d YOUR_DATABASE_NAME -f migrations/003_new.sql
```

### Monitor Resources
```bash
# Check all sites healthy
pm2 monit

# Check disk space
df -h

# Check memory
free -h
```

---

## Quick Reference

### Your Application
```bash
# Logs
pm2 logs YOUR_PROCESS_NAME

# Restart
pm2 restart YOUR_PROCESS_NAME

# Stop
pm2 stop YOUR_PROCESS_NAME

# View config
pm2 info YOUR_PROCESS_NAME
```

### Nginx
```bash
# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx

# Logs
sudo tail -f /var/log/nginx/YOUR_PROJECT_NAME.access.log
```

### Database
```bash
# Connect
psql -h localhost -U YOUR_DB_USER -d YOUR_DATABASE_NAME

# Backup
pg_dump -h localhost -U YOUR_DB_USER YOUR_DATABASE_NAME > backup.sql
```

---

## Multi-Site Summary

After deployment, the server should have:

```
Server (SERVER_IP)
├── Nginx (80/443)
│   ├── site1.com → localhost:3000
│   ├── site2.com → localhost:3001
│   └── yourdomain.com → localhost:YOUR_PORT  [NEW]
├── PM2
│   ├── site1-process (port 3000)
│   ├── site2-process (port 3001)
│   └── YOUR_PROCESS (port YOUR_PORT)  [NEW]
└── PostgreSQL
    ├── site1_db
    ├── site2_db
    └── YOUR_DATABASE_NAME  [NEW]
```

All sites operate independently but share:
- PostgreSQL server
- Global environment variables
- AWS SES (if configured)
- Postfix SMTP
- SSL certificate management

---

## Related Documentation

- **New Standalone Server**: See `deploy-new-standalone-linux-server.md`
- **Multi-Tenant Architecture**: See `deploy-multi-tenant-web-server.md`
- **AWS Lessons**: See Global-History/resolutions/aws-deployment-lessons.md
- **Email Setup**: See `email-setup-postfix-ses.md`

---

**Last Updated**: 2025-10-18  
**Status**: Production-Ready  
**Estimated Time**: 1-2 hours for existing server

