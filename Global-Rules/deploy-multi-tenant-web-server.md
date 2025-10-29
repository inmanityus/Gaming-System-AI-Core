# Deploy to Multi-Tenant AWS Linux Web Server

**Purpose**: Deploy multiple Next.js/Node.js websites to a single AWS EC2 instance with proper isolation, security, and scalability.

**Source**: Extracted from Functional Fitness USA Website deployment (October 2025)

**Validated**: Production deployment successful, serving real traffic

---

## Overview

This workflow enables hosting multiple websites on a single AWS EC2 server using:
- **Nginx** reverse proxy (routes domains to different ports)
- **PM2** process management (separate process per site)
- **PostgreSQL** shared database server (separate database per site)
- **Let's Encrypt** SSL certificates (one per domain)
- **Global + Site-Specific** environment variables

### Architecture
```
Internet → Nginx (80/443)
             ├── site1.com → localhost:3000 (Site 1)
             ├── site2.com → localhost:3001 (Site 2)
             └── site3.com → localhost:3002 (Site 3)
                                ↓
                        PostgreSQL (5432)
                        ├── site1_db
                        ├── site2_db
                        └── site3_db
```

---

## Server Specifications

### Recommended Instance Type
- **Development/Testing**: t3a.small ($15/month, 2GB RAM)
- **Production (1-3 sites)**: t3a.medium ($30/month, 4GB RAM)  
- **Production (4-8 sites)**: t3a.large ($60/month, 8GB RAM)

### Storage
- **Minimum**: 30GB gp3 SSD
- **Recommended**: 50GB+ for multiple sites with media

---

## Prerequisites

1. **AWS CLI installed and configured**
   ```bash
   aws configure
   # Enter Access Key ID, Secret Access Key, Region (us-east-1)
   ```

2. **SSH key pair created**
   ```bash
   aws ec2 create-key-pair --key-name multi-tenant-prod \
     --query 'KeyMaterial' --output text > multi-tenant-prod.pem
   chmod 400 multi-tenant-prod.pem
   ```

3. **jq installed** (JSON processor)
   ```bash
   brew install jq  # macOS
   sudo apt-get install jq  # Ubuntu
   ```

---

## Phase 1: Server Provisioning (30 minutes)

### 1.1 Create Security Group
```bash
# Get default VPC
VPC_ID=$(aws ec2 describe-vpcs --region us-east-1 \
  --filters "Name=isDefault,Values=true" \
  --query 'Vpcs[0].VpcId' --output text)

# Create security group
SG_ID=$(aws ec2 create-security-group \
  --group-name multi-tenant-web-server \
  --description "Multi-tenant web hosting security group" \
  --vpc-id $VPC_ID \
  --region us-east-1 \
  --query 'GroupId' --output text)

# Get your public IP
YOUR_IP=$(curl -s https://checkip.amazonaws.com)

# Add security rules
aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 22 --cidr ${YOUR_IP}/32 --region us-east-1

aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 80 --cidr 0.0.0.0/0 --region us-east-1

aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 443 --cidr 0.0.0.0/0 --region us-east-1
```

### 1.2 Launch EC2 Instance
```bash
# Find latest Ubuntu 22.04 AMI
AMI_ID=$(aws ec2 describe-images --region us-east-1 \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
  --query 'Images|sort_by(@, &CreationDate)[-1].ImageId' \
  --output text)

# Launch instance
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3a.medium \
  --key-name multi-tenant-prod \
  --security-group-ids $SG_ID \
  --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=50,VolumeType=gp3}" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=multi-tenant-web-server}]" \
  --region us-east-1 \
  --query 'Instances[0].InstanceId' \
  --output text)

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region us-east-1

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
  --region us-east-1 --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "Server IP: $PUBLIC_IP"
```

---

## Phase 2: Server Initialization (20 minutes)

### 2.1 Connect to Server
```bash
ssh -i multi-tenant-prod.pem ubuntu@$PUBLIC_IP
```

### 2.2 Update System & Install Base Software
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install essentials
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

---

## Phase 3: Install Software Stack (30 minutes)

### 3.1 Install Node.js 18 LTS
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version  # Should show v18.x
```

### 3.2 Install PM2
```bash
sudo npm install -g pm2
pm2 startup  # Follow instructions
```

### 3.3 Install PostgreSQL 15
```bash
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 3.4 Configure PostgreSQL for Multi-Tenant
```bash
# Use 'trust' authentication for localhost (secure & simple)
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Add this line BEFORE other host lines:
# host    all    all    127.0.0.1/32    trust

sudo systemctl reload postgresql
```

**Why trust authentication?**
- Only localhost can connect (not exposed to internet)
- No password management complexity
- PostgreSQL still validates username
- Secure for multi-site hosting

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

---

## Phase 4: Global Configuration (10 minutes)

### 4.1 Set Global Environment Variables
```bash
sudo nano /etc/environment

# Add these (shared by all sites):
SMTP_HOST=localhost
SMTP_PORT=25
NODE_ENV=production
```

### 4.2 Configure Postfix (Local SMTP)
```bash
sudo apt-get install -y postfix

# Configure as "Internet Site" or edit /etc/postfix/main.cf:
sudo nano /etc/postfix/main.cf

# Set:
inet_interfaces = loopback-only
mydestination = localhost
mynetworks = 127.0.0.0/8

sudo systemctl restart postfix
```

**Why local Postfix?**
- Simple email sending for contact forms, login codes
- Port 25 not exposed to internet (secure)
- For production emails, add AWS SES configuration

### 4.3 Create Site Directories
```bash
sudo mkdir -p /var/www
sudo chown ubuntu:ubuntu /var/www
```

---

## Phase 5: Deploy First Site (20 minutes)

### 5.1 Upload Application Code
```bash
# From local machine:
cd /path/to/your/project
tar -czf app.tar.gz --exclude=node_modules --exclude=.next --exclude=.git .

scp -i multi-tenant-prod.pem app.tar.gz ubuntu@$PUBLIC_IP:~/

# On server:
mkdir -p /var/www/site1.com
cd /var/www/site1.com
tar -xzf ~/app.tar.gz
```

### 5.2 Create Database
```bash
sudo -u postgres psql

CREATE DATABASE site1_db;
CREATE USER site1_user WITH PASSWORD 'changeme123';
GRANT ALL PRIVILEGES ON DATABASE site1_db TO site1_user;
\q
```

### 5.3 Configure Environment Variables
```bash
cd /var/www/site1.com
nano .env.local

# Site-specific variables:
DATABASE_URL=postgresql://site1_user:changeme123@localhost:5432/site1_db
NEXT_PUBLIC_BASE_URL=https://site1.com
SMTP_FROM_EMAIL=noreply@site1.com
DEFAULT_EMAIL=info@site1.com

# Will also use global variables from /etc/environment
```

### 5.4 Install Dependencies & Build
```bash
cd /var/www/site1.com
npm install --production
npm run build
```

### 5.5 Start with PM2
```bash
pm2 start npm --name "site1" -- start
pm2 save
```

### 5.6 Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/site1.com

# Add:
server {
    listen 80;
    server_name site1.com www.site1.com;
    
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

# Enable site
sudo ln -s /etc/nginx/sites-available/site1.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5.7 Setup SSL
```bash
# After DNS is pointing to server IP:
sudo certbot --nginx -d site1.com -d www.site1.com
```

**Test**: Visit https://site1.com - should load your application!

---

## Phase 6: Add Additional Sites (10 minutes each)

### For Each New Site:

1. **Create directory**: `mkdir /var/www/site2.com`
2. **Upload code**: Same as Phase 5.1
3. **Create database**: New database name `site2_db`
4. **Configure .env.local**: Use port 3001, different credentials
5. **Install & build**: `npm install && npm run build`
6. **Start with PM2**: `pm2 start npm --name "site2" -- start -- -p 3001`
7. **Add Nginx config**: Same as 5.6 but port 3001 and domain site2.com
8. **Setup SSL**: `sudo certbot --nginx -d site2.com -d www.site2.com`

### Port Assignment Strategy
- Site 1: 3000
- Site 2: 3001
- Site 3: 3002
- Site 4: 3003
- ... and so on

---

## Common Tasks

### View All Sites
```bash
pm2 status
```

### Restart Site
```bash
pm2 restart site1
```

### View Logs
```bash
pm2 logs site1
pm2 logs site1 --lines 100
```

### Update Site
```bash
cd /var/www/site1.com
git pull  # or upload new code
npm install
npm run build
pm2 restart site1
```

### Add SSL Certificate
```bash
sudo certbot --nginx -d newsite.com -d www.newsite.com
```

### Renew SSL Certificates (automatic)
```bash
# Certbot auto-renews via cron, but to test:
sudo certbot renew --dry-run
```

---

## Troubleshooting

### Site Not Loading
```bash
# Check PM2 status
pm2 status

# Check application logs
pm2 logs site1

# Check Nginx configuration
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Database Connection Issues
```bash
# Test connection
psql -h localhost -U site1_user -d site1_db

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Verify pg_hba.conf
sudo cat /etc/postgresql/15/main/pg_hba.conf | grep 127.0.0.1
```

### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
```

### Out of Memory
```bash
# Check current usage
free -h

# Add more swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Cost Analysis

### Monthly Costs (us-east-1)
- **t3a.medium**: $30/month (2 vCPU, 4GB RAM)
- **50GB gp3 storage**: $4/month
- **Data transfer**: ~$5-10/month
- **Total**: ~$40-45/month

**Per-site cost**: $10-15/month (hosting 3 sites)

### Cost Optimization
- Use t3a instances (10-15% cheaper than t3)
- Reserved instances (40% discount for 1-year commitment)
- Savings Plans (flexible discount options)

---

## Security Best Practices

1. **Keep software updated**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

2. **Monitor failed login attempts**
   ```bash
   sudo fail2ban-client status sshd
   ```

3. **Regular backups**
   ```bash
   # Database backup
   pg_dump -h localhost -U site1_user site1_db > backup.sql
   
   # Code backup
   tar -czf site-backup.tar.gz /var/www/site1.com
   ```

4. **Use environment variables for secrets**
   - Never commit .env.local files
   - Rotate passwords regularly
   - Use AWS Secrets Manager for production

5. **Enable AWS CloudWatch monitoring**
   - CPU/Memory alerts
   - Disk space alerts
   - Auto-restart on crashes

---

## Production Checklist

Before going live:
- [ ] DNS records pointing to server IP
- [ ] SSL certificates installed and auto-renewing
- [ ] Database backups configured
- [ ] CloudWatch monitoring enabled
- [ ] fail2ban configured and active
- [ ] PM2 startup script configured
- [ ] All sites tested and loading correctly
- [ ] Environment variables verified
- [ ] Email sending tested
- [ ] Contact forms working
- [ ] Authentication systems tested

---

## Related Documentation

- **AWS Direct CLI Usage**: See Global-Rules/AWS-Direct-CLI-Usage.md
- **PostgreSQL Configuration**: See Global-Workflows/postgresql-setup.md
- **Email Setup**: See Global-Workflows/email-setup-postfix-ses.md
- **Nginx Configuration**: See Global-Utils/nginx-reverse-proxy-configs/

---

**Last Updated**: 2025-10-18  
**Validated By**: Functional Fitness USA production deployment  
**Estimated Deploy Time**: First site: 2-3 hours | Additional sites: 15-30 minutes each

