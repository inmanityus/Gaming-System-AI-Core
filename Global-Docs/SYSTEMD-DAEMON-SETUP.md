# Systemd Daemon Setup for Automated Tasks
**Production-Ready Scheduled Task Execution**

## Overview

Systemd is the modern init system and service manager for Linux. This guide covers setting up automated, scheduled tasks (daemons) using systemd timers—a robust alternative to cron jobs. This approach was successfully implemented for the Innovation Forge monthly article generation daemon.

**Created:** October 19, 2025  
**Platform:** Linux (Ubuntu 20.04+)  
**Use Case:** Automated monthly article generation

---

## Why Systemd Over Cron?

### Advantages of Systemd Timers

1. **Better Logging:** Integrated with journalctl
2. **Dependencies:** Can wait for network, database, etc.
3. **Resource Management:** CPU/memory limits
4. **Persistent Timers:** Catch up on missed runs
5. **Easy Monitoring:** `systemctl status` shows everything
6. **Calendar Expressions:** More flexible than cron syntax

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│          Systemd Timer Architecture              │
│                                                  │
│  ┌─────────────────┐         ┌───────────────┐ │
│  │  .timer file    │ triggers│  .service file│ │
│  │                 │────────▶│               │ │
│  │ OnCalendar=...  │         │ ExecStart=... │ │
│  └─────────────────┘         └───────┬───────┘ │
│                                       │          │
│                              ┌────────▼────────┐│
│                              │  Your Script    ││
│                              │                 ││
│                              │ npx tsx app.ts  ││
│                              └─────────────────┘│
└─────────────────────────────────────────────────┘
```

---

## Step-by-Step Setup

### 1. Create the Service File

**Location:** `/etc/systemd/system/your-service.service`

**Template:**
```ini
[Unit]
Description=Your Service Description
After=network.target postgresql.service

[Service]
Type=oneshot
User=ubuntu
Group=ubuntu
WorkingDirectory=/path/to/your/application

# Environment
Environment="NODE_ENV=production"
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

# Load environment file
EnvironmentFile=/path/to/your/application/.env

# The command to run
ExecStart=/usr/bin/npx tsx /path/to/your/script.ts

# Logging
StandardOutput=append:/var/log/your-service/output.log
StandardError=append:/var/log/your-service/error.log

# Restart policy
Restart=no

[Install]
WantedBy=multi-user.target
```

**Example: Monthly Article Generator**
```ini
[Unit]
Description=Innovation Forge Monthly Article Generator
After=network.target postgresql.service

[Service]
Type=oneshot
User=ubuntu
Group=ubuntu
WorkingDirectory=/var/www/innovation-forge-website

Environment="NODE_ENV=production"
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

EnvironmentFile=/var/www/innovation-forge-website/.env

ExecStart=/usr/bin/npx tsx scripts/monthly-article-daemon.ts

StandardOutput=append:/var/log/innovation-forge/monthly-article-generation.log
StandardError=append:/var/log/innovation-forge/monthly-article-generation-error.log

Restart=no

[Install]
WantedBy=multi-user.target
```

### 2. Create the Timer File

**Location:** `/etc/systemd/system/your-service.timer`

**Template:**
```ini
[Unit]
Description=Timer for Your Service
Requires=your-service.service

[Timer]
# Schedule (see Calendar Expressions below)
OnCalendar=*-*-01 03:00:00

# Catch up on missed runs if system was down
Persistent=true

# Optional: Random delay to spread load
# RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

**Example: Monthly on 1st at 3AM**
```ini
[Unit]
Description=Run Monthly Article Generator on the 1st of each month
Requires=monthly-article-generator.service

[Timer]
OnCalendar=*-*-01 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### 3. Create Log Directory

```bash
sudo mkdir -p /var/log/your-service
sudo chown ubuntu:ubuntu /var/log/your-service
sudo chmod 755 /var/log/your-service
```

### 4. Enable and Start

```bash
# Reload systemd to recognize new files
sudo systemctl daemon-reload

# Enable timer (start on boot)
sudo systemctl enable your-service.timer

# Start timer now
sudo systemctl start your-service.timer

# Check status
systemctl status your-service.timer
```

---

## Calendar Expressions

### Common Schedules

```ini
# Every day at 3:00 AM
OnCalendar=*-*-* 03:00:00

# Every Monday at 9:00 AM
OnCalendar=Mon *-*-* 09:00:00

# First of every month at 3:00 AM
OnCalendar=*-*-01 03:00:00

# Every 15 minutes
OnCalendar=*-*-* *:0/15:00

# Twice daily (6 AM and 6 PM)
OnCalendar=*-*-* 06,18:00:00

# Weekdays at noon
OnCalendar=Mon..Fri *-*-* 12:00:00

# First Monday of month at 8 AM
OnCalendar=Mon *-*-01..07 08:00:00
```

### Testing Calendar Expressions

```bash
# Check when next trigger will occur
systemd-analyze calendar "*-*-01 03:00:00"

# Output:
#   Original form: *-*-01 03:00:00
#       Normalized: *-*-01 03:00:00
#     Next elapse: Sat 2025-11-01 03:00:00 UTC
```

---

## Service Configuration Options

### Service Types

```ini
# Run once and exit (most common for scheduled tasks)
Type=oneshot

# Long-running service
Type=simple

# Forking daemon
Type=forking

# Notify systemd when ready
Type=notify
```

### Restart Policies

```ini
# Never restart (oneshot tasks)
Restart=no

# Always restart on failure
Restart=on-failure

# Always restart
Restart=always

# Restart delay
RestartSec=10s
```

### Resource Limits

```ini
# Memory limit
MemoryLimit=1G

# CPU weight (1-10000)
CPUWeight=500

# Max execution time
TimeoutStartSec=600s

# Kill after timeout
KillMode=mixed
```

### Environment Management

```ini
# Inline environment variables
Environment="NODE_ENV=production"
Environment="PATH=/usr/local/bin:/usr/bin"

# Load from file
EnvironmentFile=/path/to/.env

# Multiple environment files
EnvironmentFile=/etc/default/your-service
EnvironmentFile=/var/www/app/.env
```

---

## Monitoring & Management

### Check Status

```bash
# Timer status
systemctl status your-service.timer

# Service status
systemctl status your-service.service

# List all timers
systemctl list-timers

# List specific timer with next run time
systemctl list-timers your-service.timer
```

### View Logs

```bash
# Real-time logs
sudo journalctl -u your-service.service -f

# Last 50 lines
sudo journalctl -u your-service.service -n 50

# Logs since date
sudo journalctl -u your-service.service --since "2025-10-01"

# Logs with priority (err and above)
sudo journalctl -u your-service.service -p err

# Your custom log files
tail -f /var/log/your-service/output.log
tail -f /var/log/your-service/error.log
```

### Manual Trigger

```bash
# Run service immediately (for testing)
sudo systemctl start your-service.service

# Watch progress
sudo journalctl -u your-service.service -f
```

### Stop/Disable

```bash
# Stop timer (won't trigger anymore)
sudo systemctl stop your-service.timer

# Disable timer (won't start on boot)
sudo systemctl disable your-service.timer

# Re-enable
sudo systemctl enable your-service.timer
sudo systemctl start your-service.timer
```

---

## Deployment Workflow

### Complete Setup Script

```bash
#!/bin/bash
set -e

SERVICE_NAME="your-service"
APP_DIR="/var/www/your-app"
LOG_DIR="/var/log/${SERVICE_NAME}"

echo "Setting up ${SERVICE_NAME} daemon..."

# 1. Create log directory
sudo mkdir -p ${LOG_DIR}
sudo chown ubuntu:ubuntu ${LOG_DIR}
sudo chmod 755 ${LOG_DIR}

# 2. Copy service files
sudo cp ${APP_DIR}/deployment/${SERVICE_NAME}.service /etc/systemd/system/
sudo cp ${APP_DIR}/deployment/${SERVICE_NAME}.timer /etc/systemd/system/

# 3. Set permissions
sudo chmod 644 /etc/systemd/system/${SERVICE_NAME}.service
sudo chmod 644 /etc/systemd/system/${SERVICE_NAME}.timer

# 4. Reload systemd
sudo systemctl daemon-reload

# 5. Enable and start timer
sudo systemctl enable ${SERVICE_NAME}.timer
sudo systemctl start ${SERVICE_NAME}.timer

# 6. Show status
echo ""
echo "✅ Setup complete!"
echo ""
systemctl status ${SERVICE_NAME}.timer --no-pager
echo ""
systemctl list-timers ${SERVICE_NAME}.timer --no-pager

echo ""
echo "📝 Logs location: ${LOG_DIR}"
echo "🔍 View logs: sudo journalctl -u ${SERVICE_NAME}.service -f"
echo "▶️  Test run: sudo systemctl start ${SERVICE_NAME}.service"
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check syntax errors
systemd-analyze verify /etc/systemd/system/your-service.service

# View detailed error
sudo journalctl -u your-service.service -n 50

# Common issues:
# 1. Wrong file path in ExecStart
# 2. Missing dependencies (npm, tsx, etc.)
# 3. Permission issues
# 4. Environment variables not set
```

### Timer Not Triggering

```bash
# Check timer is active
systemctl is-active your-service.timer

# Check next trigger time
systemctl list-timers your-service.timer

# Verify calendar expression
systemd-analyze calendar "your-expression-here"

# If persistent=true, check for missed runs
sudo journalctl -u your-service.service --since yesterday
```

### Script Fails in Systemd but Works Manually

**Common Causes:**
1. **Environment Differences**
   - Solution: Use EnvironmentFile or set all variables

2. **Working Directory**
   - Solution: Set WorkingDirectory explicitly

3. **PATH Issues**
   - Solution: Set full PATH or use absolute paths

4. **User/Permission Issues**
   - Solution: Verify User= and file permissions

**Debug Approach:**
```bash
# Run as systemd user
sudo -u ubuntu bash

# Check environment
env

# Try running command
cd /path/to/app
/usr/bin/npx tsx script.ts
```

### Permission Denied Errors

```bash
# Fix ownership
sudo chown -R ubuntu:ubuntu /var/www/your-app

# Fix permissions
chmod 755 /var/www/your-app
chmod 644 /var/www/your-app/.env

# Check log directory
ls -la /var/log/your-service/
```

---

## Advanced Features

### Multiple Timers for One Service

```ini
# daily-backup.timer
[Timer]
OnCalendar=*-*-* 02:00:00

# weekly-backup.timer
[Timer]
OnCalendar=Sun *-*-* 03:00:00

# Both trigger backup.service
```

### Chaining Services

```ini
# First service
[Unit]
Description=Data Collection
After=network.target

# Second service (runs after first)
[Unit]
Description=Data Processing
After=data-collection.service
Wants=data-collection.service
```

### Conditional Execution

```ini
# Only run if file exists
[Service]
ExecCondition=/usr/bin/test -f /var/run/enable-service

# Only run if not already running
[Unit]
Conflicts=my-service.service
```

### Email Notifications on Failure

```ini
[Unit]
OnFailure=status-email@%n.service

[Service]
# your service config
```

---

## Best Practices

### 1. Logging

```ini
# Always log to files
StandardOutput=append:/var/log/service/output.log
StandardError=append:/var/log/service/error.log

# Include timestamps in your script
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting task..."
```

### 2. Error Handling in Scripts

```typescript
// scripts/monthly-article-daemon.ts
async function main() {
  const startTime = Date.now();
  
  try {
    console.log(`[${new Date().toISOString()}] Starting article generation...`);
    
    await generateArticle();
    
    const duration = (Date.now() - startTime) / 1000 / 60;
    console.log(`[${new Date().toISOString()}] ✅ Completed in ${duration.toFixed(1)} minutes`);
    
    process.exit(0);
  } catch (error) {
    console.error(`[${new Date().toISOString()}] ✗ Error:`, error);
    process.exit(1);
  }
}

main();
```

### 3. Use Persistent Timers

```ini
# Catches up on missed runs
Persistent=true
```

### 4. Set Appropriate Timeouts

```ini
# Don't let tasks hang forever
TimeoutStartSec=3600s  # 1 hour max
```

### 5. Resource Limits

```ini
# Prevent runaway processes
MemoryLimit=2G
CPUQuota=50%
```

---

## Migration from Cron

### Cron to Systemd Mapping

| Cron Expression | Systemd OnCalendar |
|----------------|-------------------|
| `0 3 * * *` | `*-*-* 03:00:00` |
| `0 3 1 * *` | `*-*-01 03:00:00` |
| `*/15 * * * *` | `*-*-* *:0/15:00` |
| `0 0 * * 0` | `Sun *-*-* 00:00:00` |
| `0 9 * * 1-5` | `Mon..Fri *-*-* 09:00:00` |

### Migration Steps

1. List current cron jobs: `crontab -l`
2. Create systemd service for each job
3. Create timer with equivalent schedule
4. Test: `sudo systemctl start service-name.service`
5. Enable timer: `sudo systemctl enable service-name.timer`
6. Remove from cron: `crontab -e`

---

## Real-World Example

### Complete Innovation Forge Setup

**Directory Structure:**
```
/var/www/innovation-forge-website/
├── deployment/
│   ├── monthly-article-generator.service
│   └── monthly-article-generator.timer
├── scripts/
│   └── monthly-article-daemon.ts
├── .env
└── package.json

/var/log/innovation-forge/
├── monthly-article-generation.log
└── monthly-article-generation-error.log
```

**Service File:** (shown earlier)

**Timer File:** (shown earlier)

**Deployment:**
```bash
cd /var/www/innovation-forge-website
sudo cp deployment/*.service /etc/systemd/system/
sudo cp deployment/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable monthly-article-generator.timer
sudo systemctl start monthly-article-generator.timer
```

**Monitoring:**
```bash
# Check next run
systemctl list-timers monthly-article-generator.timer

# View last run
sudo journalctl -u monthly-article-generator.service -n 100

# Test run
sudo systemctl start monthly-article-generator.service
tail -f /var/log/innovation-forge/monthly-article-generation.log
```

---

## Security Considerations

1. **Run as Non-Root User**
   ```ini
   User=ubuntu
   Group=ubuntu
   ```

2. **Restrict Permissions**
   ```bash
   chmod 644 /etc/systemd/system/your-service.service
   chmod 644 /etc/systemd/system/your-service.timer
   ```

3. **Secure Environment Files**
   ```bash
   chmod 600 /var/www/app/.env
   chown ubuntu:ubuntu /var/www/app/.env
   ```

4. **Limit Resource Usage**
   ```ini
   MemoryLimit=1G
   CPUQuota=25%
   ```

---

## Related Documentation

- [AI-COLLABORATIVE-AUTHORING-SYSTEM.md](./AI-COLLABORATIVE-AUTHORING-SYSTEM.md) - The system using this daemon
- Official systemd documentation: https://systemd.io

---

**Last Updated:** October 19, 2025  
**Maintained By:** AI Development Team

