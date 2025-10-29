# Deploy to New Standalone Linux Server

**Purpose**: Deploy a single Next.js/Node.js website to a new AWS EC2 Ubuntu server with complete setup (PostgreSQL, Email, SSL, Security).

**Use Case**: First deployment for a new project that needs its own dedicated server.

**Alternative**: If deploying to an existing multi-tenant server, see `deploy-to-existing-multi-tenant-server.md`

---

## Overview

This guide provisions a NEW server from scratch and deploys a single website with:
- Ubuntu 22.04 LTS
- Node.js 18 LTS + PM2
- PostgreSQL 15 (one database)
- Nginx reverse proxy
- SSL certificates (Let's Encrypt)
- Email (Postfix + AWS SES optional)
- Security hardening (UFW, fail2ban, SSH)
- Environment variables (Global + Project specific)

**Estimated Time**: 2-3 hours for complete setup

**Monthly Cost**: ~$30-40 for t3a.medium instance

---

## Prerequisites

1. **AWS CLI configured**
   ```bash
   aws configure
   # Enter: Access Key ID, Secret Key, Region (us-east-1), Format (json)
   ```

2. **Project ready to deploy**
   - Code in git repository or local directory
   - `.env.local` configured
   - Database schema files ready
   - Build tested locally

3. **Domain name** (optional, can use IP initially)

---

## Phase 1: Provision AWS Infrastructure (20 minutes)

### 1.1 Create Security Group
```bash
# Get default VPC
VPC_ID=$(aws ec2 describe-vpcs --region us-east-1 \
  --filters "Name=isDefault,Values=true" \
  --query 'Vpcs[0].VpcId' --output text)

echo "VPC ID: $VPC_ID"

# Create security group
SG_ID=$(aws ec2 create-security-group \
  --group-name PROJECT_NAME-prod \
  --description "Production security group for PROJECT_NAME" \
  --vpc-id $VPC_ID \
  --region us-east-1 \
  --query 'GroupId' --output text)

echo "Security Group: $SG_ID"

# Get your IP for SSH access
YOUR_IP=$(curl -s https://checkip.amazonaws.com)
echo "Your IP: $YOUR_IP"

# Add firewall rules
aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 22 --cidr ${YOUR_IP}/32 --region us-east-1

aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 80 --cidr 0.0.0.0/0 --region us-east-1

aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 443 --cidr 0.0.0.0/0 --region us-east-1

echo "Firewall rules created"
```

### 1.2 Create SSH Key Pair
```bash
aws ec2 create-key-pair \
  --key-name PROJECT_NAME-prod \
  --region us-east-1 \
  --query 'KeyMaterial' \
  --output text > PROJECT_NAME-prod.pem

chmod 400 PROJECT_NAME-prod.pem
echo "SSH key created: PROJECT_NAME-prod.pem"
```

### 1.3 Launch EC2 Instance
```bash
# Find latest Ubuntu 22.04 AMI
AMI_ID=$(aws ec2 describe-images --region us-east-1 \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
  --query 'Images|sort_by(@, &CreationDate)[-1].ImageId' \
  --output text)

echo "Using AMI: $AMI_ID"

# Launch instance
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3a.medium \
  --key-name PROJECT_NAME-prod \
  --security-group-ids $SG_ID \
  --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=30,VolumeType=gp3}" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=PROJECT_NAME-prod}]" \
  --region us-east-1 \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "Instance ID: $INSTANCE_ID"

# Wait for instance to run
echo "Waiting for instance to start..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region us-east-1

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
  --region us-east-1 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "========================================="
echo "Server IP: $PUBLIC_IP"
echo "SSH: ssh -i PROJECT_NAME-prod.pem ubuntu@$PUBLIC_IP"
echo "========================================="

# Save deployment info
cat > deployment-info.json <<EOF
{
  "instance_id": "$INSTANCE_ID",
  "public_ip": "$PUBLIC_IP",
  "security_group": "$SG_ID",
  "key_file": "PROJECT_NAME-prod.pem",
  "region": "us-east-1"
}
EOF

echo "Deployment info saved to deployment-info.json"
```

---

## Phase 2: Initialize Server (30 minutes)

### 2.1 Connect to Server
```bash
# Wait 2-3 minutes for cloud-init to complete
sleep 120

ssh -i PROJECT_NAME-prod.pem ubuntu@$PUBLIC_IP
```

### 2.2 Update System
```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y curl wget git vim htop ufw fail2ban \
  unattended-upgrades ca-certificates gnupg build-essential
```

### 2.3 Configure Firewall
```bash
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw --force enable
```

### 2.4 Harden SSH
```bash
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

### 2.5 Configure Automatic Updates
```bash
sudo dpkg-reconfigure -plow unattended-upgrades

cat | sudo tee /etc/apt/apt.conf.d/20auto-upgrades > /dev/null <<EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF
```

---

## Phase 3: Install Software Stack (30 minutes)

### 3.1 Install Node.js 18 LTS
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version  # Verify v18.x
npm --version
```

### 3.2 Install PM2
```bash
sudo npm install -g pm2
pm2 startup  # Follow instructions to enable autostart
```

### 3.3 Install PostgreSQL 15
```bash
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 3.4 Configure PostgreSQL
```bash
# Use trust authentication for localhost (secure and simple)
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Add this line BEFORE other host lines:
# host    all    all    127.0.0.1/32    trust

sudo systemctl reload postgresql
```

### 3.5 Install Nginx
```bash
sudo apt-get install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 3.6 Install Certbot (SSL)
```bash
sudo apt-get install -y certbot python3-certbot-nginx
```

### 3.7 Install Postfix (Optional - Local SMTP)
```bash
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y postfix

# Configure for localhost only
sudo postconf -e "inet_interfaces = loopback-only"
sudo postconf -e "mydestination = localhost"
sudo postconf -e "mynetworks = 127.0.0.0/8"
sudo systemctl restart postfix
```

---

## Phase 4: Setup Global Environment Variables (10 minutes)

### 4.1 Create Global Variables
```bash
sudo nano /etc/environment

# Add these global variables (shared across all processes):
NODE_ENV=production
PGPASSWORD=YOUR_POSTGRES_PASSWORD
SMTP_HOST=localhost
SMTP_PORT=25

# Optional - AWS SES credentials (if using)
AWS_SES_SMTP_USER=AKIA...
AWS_SES_SMTP_PASSWORD=...

# Save and exit
```

### 4.2 Load Environment
```bash
source /etc/environment
```

---

## Phase 5: Create Database (10 minutes)

### 5.1 Create Database and User
```bash
# Database name: Use project name with underscores
# Example: innovation_forge_website

sudo -u postgres psql

CREATE DATABASE PROJECT_DATABASE_NAME;
CREATE USER PROJECT_DB_USER WITH PASSWORD 'SECURE_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE PROJECT_DATABASE_NAME TO PROJECT_DB_USER;
\q
```

### 5.2 Test Connection
```bash
psql -h localhost -U PROJECT_DB_USER -d PROJECT_DATABASE_NAME -c "SELECT version();"
```

---

## Phase 6: Deploy Application (30 minutes)

### 6.1 Create Application Directory
```bash
sudo mkdir -p /var/www/PROJECT_NAME
sudo chown ubuntu:ubuntu /var/www/PROJECT_NAME
```

### 6.2 Upload Code
**From local machine:**
```bash
cd /path/to/your/project
tar -czf app.tar.gz --exclude=node_modules --exclude=.next --exclude=.git .
scp -i PROJECT_NAME-prod.pem app.tar.gz ubuntu@$PUBLIC_IP:~/
```

**On server:**
```bash
cd /var/www/PROJECT_NAME
tar -xzf ~/app.tar.gz
rm ~/app.tar.gz
```

### 6.3 Create Project-Specific .env.local
```bash
cd /var/www/PROJECT_NAME
nano .env.local

# Project-specific variables:
DATABASE_URL=postgresql://PROJECT_DB_USER:SECURE_PASSWORD@localhost:5432/PROJECT_DATABASE_NAME
NEXT_PUBLIC_BASE_URL=https://yourdomain.com
SMTP_FROM_EMAIL=noreply@yourdomain.com
DEFAULT_EMAIL=info@yourdomain.com

# Any project-specific API keys, etc.
```

### 6.4 Load Database Schema
```bash
cd /var/www/PROJECT_NAME

# If you have migration files:
psql -h localhost -U PROJECT_DB_USER -d PROJECT_DATABASE_NAME -f migrations/001_initial.sql

# Or if you have a full database dump:
psql -h localhost -U PROJECT_DB_USER -d PROJECT_DATABASE_NAME < database-dump.sql
```

### 6.5 Install Dependencies and Build
```bash
cd /var/www/PROJECT_NAME
npm install --production
npm run build
```

### 6.6 Start with PM2
```bash
cd /var/www/PROJECT_NAME
pm2 start npm --name "PROJECT_NAME" -- start
pm2 save
pm2 list  # Verify running
```

---

## Phase 7: Configure Nginx (15 minutes)

### 7.1 Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/yourdomain.com

# Add this configuration:
```

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:3000;
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

### 7.2 Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/yourdomain.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7.3 Test HTTP Access
```bash
curl http://$PUBLIC_IP
# Should show your website
```

---

## Phase 8: Setup SSL Certificate (10 minutes)

### 8.1 Configure DNS
**Before running certbot, configure your domain DNS:**
- Add A record: `yourdomain.com` → `$PUBLIC_IP`
- Add A record: `www.yourdomain.com` → `$PUBLIC_IP`
- Wait 5-10 minutes for DNS propagation

### 8.2 Verify DNS
```bash
dig yourdomain.com +short
# Should show $PUBLIC_IP
```

### 8.3 Install SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts:
# - Enter email address
# - Agree to terms
# - Choose redirect HTTP to HTTPS (recommended: yes)
```

### 8.4 Test HTTPS
```bash
curl https://yourdomain.com
```

### 8.5 Setup Auto-Renewal
```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically creates a systemd timer for renewal
sudo systemctl status certbot.timer
```

---

## Phase 9: Final Configuration (15 minutes)

### 9.1 Test Application
- Visit https://yourdomain.com
- Test all pages
- Test contact forms
- Test database operations
- Check PM2 logs: `pm2 logs PROJECT_NAME`

### 9.2 Configure Log Rotation
```bash
sudo nano /etc/logrotate.d/PROJECT_NAME

# Add:
/var/www/PROJECT_NAME/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
    sharedscripts
}
```

### 9.3 Setup Monitoring (Optional)
```bash
# CloudWatch agent for AWS monitoring
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
# Configure as needed
```

---

## Phase 10: Backup Strategy (10 minutes)

### 10.1 Database Backup Script
```bash
mkdir -p /home/ubuntu/backups
nano /home/ubuntu/backup-database.sh
```

```bash
#!/bin/bash
# Database backup script
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d-%H%M%S)
pg_dump -h localhost -U PROJECT_DB_USER PROJECT_DATABASE_NAME > "$BACKUP_DIR/db-$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "db-*.sql" -mtime +7 -delete
```

```bash
chmod +x /home/ubuntu/backup-database.sh

# Add to crontab (daily at 2am)
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup-database.sh
```

### 10.2 Code Backup
```bash
# Ensure code is in git
cd /var/www/PROJECT_NAME
git remote -v  # Verify git remote configured
```

---

## Quick Reference

### Common Commands
```bash
# Application
pm2 status
pm2 logs PROJECT_NAME
pm2 restart PROJECT_NAME
pm2 stop PROJECT_NAME

# Nginx
sudo systemctl status nginx
sudo nginx -t
sudo systemctl reload nginx

# Database
psql -h localhost -U PROJECT_DB_USER -d PROJECT_DATABASE_NAME
sudo systemctl status postgresql

# Logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
pm2 logs PROJECT_NAME --lines 100

# System
htop
df -h
free -h
```

### Deployment Info
- **Server IP**: `$PUBLIC_IP`
- **SSH**: `ssh -i PROJECT_NAME-prod.pem ubuntu@$PUBLIC_IP`
- **Application Path**: `/var/www/PROJECT_NAME`
- **Database**: `PROJECT_DATABASE_NAME`
- **PM2 Process**: `PROJECT_NAME`

---

## Troubleshooting

### Application Not Starting
```bash
pm2 logs PROJECT_NAME
# Check for errors
# Common: missing environment variables, database connection
```

### Database Connection Failed
```bash
# Verify pg_hba.conf has trust for 127.0.0.1
sudo cat /etc/postgresql/15/main/pg_hba.conf | grep 127.0.0.1
sudo systemctl reload postgresql
```

### Nginx 502 Bad Gateway
```bash
# Application not running
pm2 status
pm2 restart PROJECT_NAME
```

### SSL Certificate Issues
```bash
sudo certbot certificates
sudo certbot renew
```

---

## Post-Deployment Checklist

- [ ] Application accessible via HTTPS
- [ ] All pages load correctly
- [ ] Database queries working
- [ ] Contact forms submitting
- [ ] Email sending (if configured)
- [ ] SSL certificate valid
- [ ] PM2 auto-start configured
- [ ] Backups configured
- [ ] Monitoring configured (optional)
- [ ] DNS properly configured
- [ ] Security hardening complete

---

## Related Documentation

- **Multi-Tenant Deployment**: See `deploy-multi-tenant-web-server.md`
- **Deploy to Existing Server**: See `deploy-to-existing-multi-tenant-server.md`
- **AWS Deployment Lessons**: See Global-History/resolutions/aws-deployment-lessons.md

---

**Last Updated**: 2025-10-18  
**Status**: Production-Ready  
**Estimated Time**: 2-3 hours for complete setup

