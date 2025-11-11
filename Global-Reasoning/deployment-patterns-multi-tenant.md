# Multi-Tenant Deployment Patterns
**Reusable Strategies for Deploying Multiple Applications on Shared Infrastructure**

**Created:** October 19, 2025  
**Source:** Innovation Forge Website deployment  
**Applicability:** All multi-tenant web application deployments

---

## Core Principle

**When deploying multiple applications on a single server, isolation and namespacing are critical at every level: ports, databases, environment variables, and resources.**

---

## Pattern 1: Environment Variable Namespacing

### Problem
Multiple applications on same server need different configurations for same services (e.g., SMTP, database, API keys).

### Anti-Pattern (Causes Conflicts)
```bash
# /etc/environment (GLOBAL)
SMTP_HOST=localhost
SMTP_PORT=25
DATABASE_URL=postgres://localhost/app1

# Project A .env
SMTP_HOST=smtp.gmail.com  # ❌ Overridden by global!
SMTP_PORT=587             # ❌ Overridden by global!
```

### Solution: Prefix-Based Namespacing

**Global Variables (Infrastructure Level):**
```bash
# /etc/environment
AWS_SES_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
AWS_SES_SMTP_PORT=587
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

**Project Variables (Application Level):**
```env
# Project A .env
AWS_SES_SMTP_USER=projecta_user
AWS_SES_SMTP_PASSWORD=projecta_pass
DATABASE_URL=postgresql://projecta_user:pass@localhost/projecta_db
```

**Application Code (Priority Order):**
```typescript
const smtpConfig = {
  host: process.env.AWS_SES_SMTP_HOST ||  // Prefixed global (safe)
        process.env.SMTP_HOST ||           // Project override
        'localhost',                       // Fallback
  port: process.env.AWS_SES_SMTP_PORT ||
        process.env.SMTP_PORT ||
        587,
  user: process.env.AWS_SES_SMTP_USER,    // Always project-specific
  pass: process.env.AWS_SES_SMTP_PASSWORD  // Always project-specific
};
```

### Naming Convention
- **Global:** `TECHNOLOGY_SERVICE_PROPERTY` (e.g., `AWS_SES_SMTP_HOST`)
- **Project:** `SERVICE_PROPERTY` or `PROJECT_SERVICE_PROPERTY`
- **Never:** Generic names in global scope (`SMTP_HOST`, `DB_HOST`)

### When to Use
- ✅ Multi-tenant servers
- ✅ Shared development machines
- ✅ CI/CD pipelines with multiple projects
- ✅ Docker compose with multiple services

---

## Pattern 2: Port Range Allocation

### Problem
Multiple applications need to listen on ports without conflicts.

### Solution: Systematic Port Ranges

**System Ports (Reserved):**
```
22:    SSH
80:    HTTP (Nginx)
443:   HTTPS (Nginx)
5432:  PostgreSQL
6379:  Redis (if used)
```

**Application Ports (Ranges per Project):**
```
3000-3010: Project 1
3011-3020: Project 2
3021-3030: Project 3
...
4000-4010: Project 1 (additional services)
4011-4020: Project 2 (additional services)
```

**Within Project Range:**
```
3000: Main web application
3001: API server (if separate)
3002: Admin panel (if separate)
3003: Websocket server
3004: Background job processor UI
...
```

**Documentation Format:**
```markdown
# project-services.md

| Project              | Port | Service Type |
|---------------------|------|--------------|
| Functional Fitness  | 3010 | Next.js Web  |
| Innovation Forge    | 3000 | Next.js Web  |
| Project Three       | 3020 | Next.js Web  |
| Project Three API   | 3021 | Express API  |
```

**Nginx Configuration:**
```nginx
# Domain → Port mapping
innovationforge.ai → localhost:3000
befreefitness.ai   → localhost:3010
projectthree.com   → localhost:3020
```

### When to Use
- ✅ Always for multi-tenant deployments
- ✅ Development environments with multiple projects
- ✅ Kubernetes/Docker with multiple containers

---

## Pattern 3: Database Isolation

### Problem
Applications need separate databases for security and data integrity.

### Solution: Per-Project Database and User

**Setup Script:**
```sql
-- Project A
CREATE DATABASE projecta_db;
CREATE USER projecta_user WITH PASSWORD 'strong_password_a';
GRANT ALL PRIVILEGES ON DATABASE projecta_db TO projecta_user;
\c projecta_db
GRANT ALL ON SCHEMA public TO projecta_user;

-- Project B
CREATE DATABASE projectb_db;
CREATE USER projectb_user WITH PASSWORD 'strong_password_b';
GRANT ALL PRIVILEGES ON DATABASE projectb_db TO projectb_user;
\c projectb_db
GRANT ALL ON SCHEMA public TO projectb_user;
```

**Access Restrictions (pg_hba.conf):**
```conf
# Project A user can only access Project A database
local   projecta_db     projecta_user                   md5
local   projectb_db     projectb_user                   md5

# Explicitly deny cross-project access
local   projecta_db     projectb_user                   reject
local   projectb_db     projecta_user                   reject
```

**Connection Strings:**
```env
# Project A .env
DATABASE_URL=postgresql://projecta_user:password@localhost:5432/projecta_db

# Project B .env
DATABASE_URL=postgresql://projectb_user:password@localhost:5432/projectb_db
```

### Benefits
- 🔒 **Security:** One compromised app can't access other databases
- 🛡️ **Data Integrity:** No accidental cross-project queries
- 📊 **Resource Tracking:** Per-project database size and performance
- 🔄 **Migration Safety:** Migrations only affect one project

### When to Use
- ✅ Always for production multi-tenant
- ✅ Shared development/staging environments
- ✅ When projects have different data compliance requirements

---

## Pattern 4: Process Management with PM2

### Problem
Need to manage multiple Node.js processes with different configurations.

### Solution: Named PM2 Applications

**Per-Project PM2 Config:**
```javascript
// /var/www/projecta/pm2.config.js
module.exports = {
  apps: [{
    name: 'projecta',
    script: 'node_modules/next/dist/bin/next',
    args: 'start',
    env: {
      NODE_ENV: 'production',
      PORT: 3000,
    },
    instances: 1,
    exec_mode: 'fork',
    max_memory_restart: '1G',
    error_file: '/var/log/projecta/error.log',
    out_file: '/var/log/projecta/output.log',
  }]
};

// /var/www/projectb/pm2.config.js
module.exports = {
  apps: [{
    name: 'projectb',
    script: 'node_modules/next/dist/bin/next',
    args: 'start',
    env: {
      NODE_ENV: 'production',
      PORT: 3010,
    },
    instances: 1,
    exec_mode: 'fork',
    max_memory_restart: '1G',
    error_file: '/var/log/projectb/error.log',
    out_file: '/var/log/projectb/output.log',
  }]
};
```

**Management Commands:**
```bash
# List all processes
pm2 list

# Manage specific project
pm2 restart projecta
pm2 logs projecta
pm2 stop projecta

# Resource monitoring
pm2 monit
```

### Isolation Benefits
- 📝 **Separate Logs:** Each project has own log files
- 🔄 **Independent Restarts:** Restart one without affecting others
- 📊 **Resource Limits:** Per-project memory limits
- ⚙️ **Different Configurations:** Each project can have unique settings

### When to Use
- ✅ Multi-tenant Node.js deployments
- ✅ Microservices on single server
- ✅ Development servers running multiple projects

---

## Pattern 5: Nginx Virtual Host Per Domain

### Problem
Multiple domains need to route to different applications on same server.

### Solution: Separate Virtual Host Files

**File Structure:**
```
/etc/nginx/sites-available/
├── domaina.com
├── domainb.com
└── domainc.com

/etc/nginx/sites-enabled/
├── domaina.com → ../sites-available/domaina.com
├── domainb.com → ../sites-available/domainb.com
└── domainc.com → ../sites-available/domainc.com
```

**Template Per Domain:**
```nginx
# /etc/nginx/sites-available/domaina.com

# HTTP → HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name domaina.com www.domaina.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS main
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name domaina.com www.domaina.com;

    # SSL
    ssl_certificate /etc/letsencrypt/live/domaina.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/domaina.com/privkey.pem;

    # Logging
    access_log /var/log/nginx/domaina.access.log;
    error_log /var/log/nginx/domaina.error.log;

    # Proxy to application
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Deployment Workflow:**
```bash
# 1. Create config
sudo nano /etc/nginx/sites-available/domaina.com

# 2. Test syntax
sudo nginx -t

# 3. Enable site
sudo ln -s /etc/nginx/sites-available/domaina.com /etc/nginx/sites-enabled/

# 4. Reload nginx
sudo systemctl reload nginx

# 5. Get SSL certificate
sudo certbot --nginx -d domaina.com -d www.domaina.com
```

### Benefits
- 🔒 **Separate SSL Certificates:** Each domain has own cert
- 📝 **Independent Logs:** Per-domain access/error logs
- ⚙️ **Custom Configuration:** Different settings per domain
- 🛠️ **Easy Maintenance:** Edit one site without affecting others

---

## Pattern 6: Systemd Service Isolation

### Problem
Multiple projects need scheduled tasks (cron jobs, daemons).

### Solution: Per-Project Systemd Services

**Naming Convention:**
```
<project>-<task>.service
<project>-<task>.timer

Examples:
- projecta-backup.service / projecta-backup.timer
- projectb-article-generator.service / projectb-article-generator.timer
```

**Service Template:**
```ini
[Unit]
Description=Project A - Task Name
After=network.target postgresql.service

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/var/www/projecta
EnvironmentFile=/var/www/projecta/.env
ExecStart=/usr/bin/npx tsx scripts/task.ts
StandardOutput=append:/var/log/projecta/task.log
StandardError=append:/var/log/projecta/task-error.log
```

**Timer Template:**
```ini
[Unit]
Description=Run Project A Task
Requires=projecta-task.service

[Timer]
OnCalendar=*-*-01 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Management
```bash
# List all timers
systemctl list-timers

# Manage specific project
systemctl start projecta-task.service
systemctl status projecta-task.timer
journalctl -u projecta-task.service -n 50
```

### Benefits
- 📋 **Organization:** Clear ownership of tasks
- 📝 **Separate Logs:** Per-project task logs
- ⚙️ **Independent Schedules:** Different timing per project
- 🛠️ **Easy Debugging:** Isolate issues to specific project

---

## Pattern 7: Log Directory Structure

### Problem
Logs from multiple projects get mixed together.

### Solution: Hierarchical Log Structure

**Directory Structure:**
```
/var/log/
├── projecta/
│   ├── access.log
│   ├── error.log
│   ├── task.log
│   └── task-error.log
├── projectb/
│   ├── access.log
│   ├── error.log
│   ├── task.log
│   └── task-error.log
└── nginx/
    ├── projecta.access.log
    ├── projecta.error.log
    ├── projectb.access.log
    └── projectb.error.log
```

**Setup Script:**
```bash
# Create log directories
sudo mkdir -p /var/log/projecta
sudo mkdir -p /var/log/projectb

# Set ownership
sudo chown -R ubuntu:ubuntu /var/log/projecta
sudo chown -R ubuntu:ubuntu /var/log/projectb

# Set permissions
sudo chmod 755 /var/log/projecta
sudo chmod 755 /var/log/projectb
```

**Log Rotation:**
```
# /etc/logrotate.d/projecta
/var/log/projecta/*.log {
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

### Benefits
- 🔍 **Easy Debugging:** Quickly find project-specific logs
- 🗄️ **Organized:** Clean separation of concerns
- 💾 **Disk Management:** Per-project log size tracking
- 🔒 **Security:** Different permission levels if needed

---

## Pattern 8: Deployment Script Template

### Problem
Need consistent deployment process across projects.

### Solution: Standardized Deployment Script

**Template:**
```bash
#!/bin/bash
set -e

# Configuration
PROJECT_NAME="projecta"
PROJECT_DIR="/var/www/$PROJECT_NAME"
DOMAIN="domaina.com"
PORT=3000
DB_NAME="${PROJECT_NAME//-/_}_db"
DB_USER="${PROJECT_NAME//-/_}_user"

echo "=== Deploying $PROJECT_NAME ==="

# 1. Upload and extract
echo "1. Extracting application..."
tar -xzf source.tar.gz -C $PROJECT_DIR
cd $PROJECT_DIR

# 2. Install dependencies
echo "2. Installing dependencies..."
npm ci --omit=dev

# 3. Setup database
echo "3. Setting up database..."
psql -h localhost -U $DB_USER -d $DB_NAME < migrations/001_init.sql

# 4. Configure environment
echo "4. Configuring environment..."
cat > .env << EOF
NODE_ENV=production
PORT=$PORT
DATABASE_URL=postgresql://$DB_USER:password@localhost/$DB_NAME
# ... other variables
EOF
chmod 600 .env

# 5. Start with PM2
echo "5. Starting application..."
pm2 start pm2.config.js
pm2 save

# 6. Configure Nginx
echo "6. Configuring Nginx..."
sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 7. Setup SSL
echo "7. Setting up SSL..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos

# 8. Verify
echo "8. Verifying deployment..."
sleep 5
curl -I https://$DOMAIN

echo "=== ✅ Deployment Complete ==="
```

---

## Anti-Patterns to Avoid

### ❌ Sharing Configuration Files
```bash
# BAD: All projects use same .env
/var/www/.env-shared

# GOOD: Each project has own .env
/var/www/projecta/.env
/var/www/projectb/.env
```

### ❌ Generic Service Names
```bash
# BAD: Ambiguous naming
sudo systemctl start article-generator.service  # Which project?

# GOOD: Project-specific naming
sudo systemctl start projecta-article-generator.service
```

### ❌ Shared Log Files
```bash
# BAD: Mixed logs
/var/log/application.log

# GOOD: Separate logs
/var/log/projecta/application.log
/var/log/projectb/application.log
```

### ❌ Hardcoded Paths in Global Configs
```bash
# BAD in /etc/environment
APP_DIR=/var/www/projecta  # Breaks other projects!

# GOOD: Each project sets own APP_DIR in .env
```

---

## Quick Reference Checklist

When deploying new project to multi-tenant server:

- [ ] Assign unique port range (document in project-services.md)
- [ ] Create dedicated database and user
- [ ] Use prefixed global variables for shared infrastructure
- [ ] Create project-specific .env with credentials
- [ ] Create separate Nginx virtual host
- [ ] Create separate PM2 config with unique app name
- [ ] Create project log directory
- [ ] Use project-prefixed systemd services
- [ ] Test isolation (env vars, ports, database access)
- [ ] Document all project-specific configurations

---

## Conclusion

Multi-tenant deployments require discipline and consistency. Following these patterns ensures:

- 🔒 **Security:** Projects can't access each other's resources
- 🛡️ **Stability:** One project's issues don't affect others  
- 📊 **Maintainability:** Clear ownership and organization
- 🔍 **Debuggability:** Easy to isolate and fix issues
- 📈 **Scalability:** Easy to add new projects

**Key Principle:** Namespace everything. Isolate everything. Document everything.

---

**Created:** October 19, 2025  
**Pattern Category:** Deployment  
**Confidence:** High (Production-tested)  
**Reusability:** Universal (applies to all multi-tenant scenarios)

