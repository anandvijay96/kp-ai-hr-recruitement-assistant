# VM Technical Specifications - AI HR Assistant

**📅 Date:** October 13, 2025  
**🎯 Purpose:** Technical requirements for production VM (OVH or similar)  
**🎯 Deployment Strategy:** Internal team pilot (10 members) → White label product

---

## 📋 Deployment Phases

### **Phase 1: Internal Team Pilot (Current)**
- **Users:** 10 internal team members
- **Purpose:** Testing, feedback gathering, refinement
- **Duration:** 2-3 months
- **Configuration:** Cost-optimized for small team

### **Phase 2: White Label Product (Future)**
- **Users:** Multiple client organizations
- **Purpose:** Commercial product offering
- **Configuration:** Scalable, multi-tenant ready

---

## 💻 Operating System Requirements

### **Recommended OS:**
```
Ubuntu Server 22.04 LTS (64-bit)
```

**Why Ubuntu 22.04 LTS:**
- ✅ Long-term support until April 2027
- ✅ Stable and well-tested
- ✅ Excellent Python 3.10/3.11 support
- ✅ Large community and documentation
- ✅ Easy package management (apt)
- ✅ Security updates for 5 years

### **Alternative Options:**
```
1. Ubuntu Server 24.04 LTS (newer, supported until 2029)
2. Debian 12 (Bookworm) - More conservative
3. Rocky Linux 9 / AlmaLinux 9 - RHEL-based alternative
```

**Not Recommended:**
- ❌ CentOS (discontinued)
- ❌ Windows Server (unnecessary licensing cost)
- ❌ Older Ubuntu versions (16.04, 18.04, 20.04)

---

## 🖥️ VM Specifications

### **PHASE 1: Internal Team Configuration (10 users)** ⭐ **START HERE**

```yaml
CPU:        2 vCPUs (2.0 GHz or higher)
RAM:        4 GB
Storage:    40 GB SSD
            - OS: 15 GB
            - Application: 8 GB
            - Database: 8 GB
            - Logs: 3 GB
            - Temp/Cache: 3 GB
            - Buffer: 3 GB
Network:    100 Mbps
Backup:     Yes (weekly manual or automated)
```

**Expected Performance:**
- Concurrent users: 5-10
- Requests/second: 20-50
- Database size: Up to 5 GB
- File storage: Up to 5 GB resumes (~10,000 resumes)
- Response time: < 500ms

**Cost Estimate (OVH VPS Starter):**
- Monthly: €6-8 (~₹550-700)
- Annually: €72-96 (~₹6,600-8,800)

**Why This Configuration:**
- ✅ **Cost-effective** for pilot phase
- ✅ **Sufficient** for 10 internal users
- ✅ **Easy to upgrade** when moving to Phase 2
- ✅ **Low risk** investment for testing
- ✅ **Fast deployment** (can be set up in 2-3 hours)

**Limitations:**
- ⚠️ Not suitable for > 20 concurrent users
- ⚠️ Limited storage for large resume volumes
- ⚠️ Basic performance (acceptable for internal use)

**When to Upgrade:**
- Team grows beyond 15 members
- Processing > 500 resumes/day
- Response time > 1 second
- Storage > 30 GB used
- Moving to white label product

---

### **PHASE 2: White Label Product - Small Client (20-50 users)**

```yaml
CPU:        2 vCPUs (2.0 GHz or higher)
RAM:        4 GB
Storage:    60 GB SSD
            - OS: 20 GB
            - Application: 10 GB
            - Database: 15 GB
            - Logs: 5 GB
            - Temp/Cache: 5 GB
            - Buffer: 5 GB
Network:    100 Mbps
```

**Expected Performance:**
- Concurrent users: 20-30
- Requests/second: 50-100
- Database size: Up to 10 GB
- File storage: Up to 20 GB resumes

**Cost Estimate:** €8-12/month (~₹700-1,100)

---

### **PHASE 2: White Label Product - Medium Client (100-200 users)**

```yaml
CPU:        4 vCPUs (2.4 GHz or higher)
RAM:        8 GB
Storage:    120 GB SSD
            - OS: 25 GB
            - Application: 15 GB
            - Database: 40 GB
            - Logs: 10 GB
            - Temp/Cache: 10 GB
            - Buffer: 20 GB
Network:    500 Mbps
```

**Expected Performance:**
- Concurrent users: 50-100
- Requests/second: 200-500
- Database size: Up to 50 GB
- File storage: Up to 50 GB resumes

**Cost Estimate:** €12-18/month (~₹1,100-1,600)

---

### **PHASE 2: White Label Product - Large Client (500+ users)**

```yaml
CPU:        8 vCPUs (2.8 GHz or higher)
RAM:        16 GB
Storage:    250 GB SSD
            - OS: 30 GB
            - Application: 20 GB
            - Database: 100 GB
            - Logs: 20 GB
            - Temp/Cache: 20 GB
            - Buffer: 60 GB
Network:    1 Gbps
```

**Expected Performance:**
- Concurrent users: 200-500
- Requests/second: 1000-2000
- Database size: Up to 150 GB
- File storage: Up to 100 GB resumes

**Cost Estimate:** €24-35/month (~₹2,200-3,200)

---

## 📊 Storage Breakdown

### **Phase 1: Internal Team (40 GB):**

```
/                   15 GB   (OS + system files)
/var/log            3 GB    (Application logs)
/var/lib/postgresql 8 GB    (Database)
/opt/hr-assistant   8 GB    (Application code)
/var/uploads        5 GB    (Resume files - ~10,000 resumes)
/tmp                1 GB    (Temporary files)
Swap                2 GB    (Virtual memory)
```

### **Storage Growth Estimates (Internal Team):**

**Database Growth:**
- 10 users × 500 KB = 5 MB
- 100 jobs × 100 KB = 10 MB
- 10,000 resumes × 50 KB metadata = 500 MB
- **Total Year 1:** ~1 GB

**File Storage Growth:**
- 10,000 resumes × 300 KB average = 3 GB
- **Total Year 1:** ~3-5 GB

**Conclusion:** 40 GB is sufficient for 2-3 years of internal use

---

### **Phase 2: White Label - Medium Client (120 GB):**

```
/                   25 GB   (OS + system files)
/var/log            10 GB   (Application logs)
/var/lib/postgresql 40 GB   (Database)
/opt/hr-assistant   15 GB   (Application code)
/var/uploads        20 GB   (Resume files)
/tmp                5 GB    (Temporary files)
Swap                4 GB    (Virtual memory)
Buffer              1 GB    (Reserved)
```

---
Swap                4 GB    (Virtual memory)
Buffer              1 GB    (Reserved)
```

### **Storage Growth Estimates:**

**Database Growth:**
- Per user: ~500 KB
- Per job posting: ~100 KB
- Per resume: ~50 KB (metadata only)
- Per match record: ~10 KB
- **Estimated:** 1 GB per 1000 users/year

**File Storage Growth:**
- Per resume (PDF): 200-500 KB average
- Per 1000 resumes: ~300 MB
- **Estimated:** 3 GB per 10,000 resumes

---

## 🔧 Required Software Stack

### **System Packages:**
```bash
# Base system
build-essential
git
curl
wget
vim / nano

# Python
python3.11
python3.11-venv
python3.11-dev
python3-pip

# Database
postgresql-14
postgresql-contrib
libpq-dev

# Web server
nginx
certbot
python3-certbot-nginx

# Process management
supervisor

# Security
ufw
fail2ban
unattended-upgrades

# Monitoring
htop
iotop
nethogs

# Optional
redis-server (for caching)
```

### **Python Packages:**
```bash
# Core framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
gunicorn==21.2.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# File processing
python-docx==1.1.0
PyPDF2==3.0.1
openpyxl==3.1.2

# AI/ML
openai==1.3.5
sentence-transformers==2.2.2
scikit-learn==1.3.2

# Background tasks
celery==5.3.4
redis==5.0.1

# Email
sendgrid==6.11.0

# Utilities
python-dotenv==1.0.0
requests==2.31.0
pydantic==2.5.0
```

---

## 🔒 Security Configuration

### **Firewall Rules (UFW):**
```bash
# Default policies
ufw default deny incoming
ufw default allow outgoing

# SSH (restrict to specific IPs if possible)
ufw allow 22/tcp

# HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# PostgreSQL (only if external access needed)
# ufw allow from <trusted-ip> to any port 5432

# Enable firewall
ufw enable
```

### **SSH Hardening:**
```bash
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
Port 22 (or custom port)
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
```

### **Fail2ban Configuration:**
```bash
# Protect SSH
[sshd]
enabled = true
maxretry = 3
bantime = 3600

# Protect Nginx
[nginx-http-auth]
enabled = true
maxretry = 5
bantime = 3600
```

---

## 🌐 Network Requirements

### **Bandwidth Estimates:**

**Per User Session:**
- Initial page load: 2-3 MB
- API calls: 10-50 KB per request
- Resume upload: 200-500 KB
- Resume download: 200-500 KB

**Monthly Bandwidth (500 users):**
- Active users/day: 100
- Sessions/user/day: 3
- Data/session: 5 MB
- **Total:** ~45 GB/month (with buffer: 100 GB/month)

### **Recommended:**
- **Minimum:** 100 GB/month
- **Recommended:** 500 GB/month
- **Production:** 1 TB/month

---

## 💾 Backup Requirements

### **Backup Storage:**
```
Database backups:  10 GB (7 daily + 4 weekly)
File backups:      20 GB (weekly full backup)
Config backups:    1 GB (version controlled)
Total:             31 GB
```

### **Backup Schedule:**
```bash
# Database
Daily:   Full backup, keep 7 days
Weekly:  Full backup, keep 4 weeks
Monthly: Full backup, keep 3 months

# Files
Weekly:  Incremental backup
Monthly: Full backup

# Configuration
On change: Git commit + push
```

---

## 🔄 Swap Space

### **Recommended Swap:**
```
RAM 4 GB  → Swap 4 GB  (1:1 ratio)
RAM 8 GB  → Swap 4 GB  (0.5:1 ratio)
RAM 16 GB → Swap 4 GB  (0.25:1 ratio)
```

### **Swap Configuration:**
```bash
# Create swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Optimize swappiness
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

---

## 📈 Performance Tuning

### **PostgreSQL Configuration:**
```bash
# /etc/postgresql/14/main/postgresql.conf

# Memory settings (for 8 GB RAM)
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
work_mem = 32MB

# Connection settings
max_connections = 100

# Performance
random_page_cost = 1.1  # For SSD
effective_io_concurrency = 200

# WAL settings
wal_buffers = 16MB
checkpoint_completion_target = 0.9
```

### **Nginx Configuration:**
```nginx
# /etc/nginx/nginx.conf

worker_processes auto;
worker_connections 1024;

# Gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript;

# Client settings
client_max_body_size 10M;  # For resume uploads
client_body_timeout 60s;
```

### **Uvicorn/Gunicorn:**
```bash
# Number of workers
Workers = (2 x CPU cores) + 1

# For 4 vCPUs
workers = 9

# Worker class
worker_class = uvicorn.workers.UvicornWorker

# Timeout
timeout = 120
```

---

## 🎯 OVH-Specific Recommendations

### **OVH VPS Options:**

#### **VPS Starter (Minimum):**
```
vCores: 2
RAM:    4 GB
SSD:    80 GB
Price:  ~€6-8/month
```
**Good for:** Development, small teams (< 50 users)

---

#### **VPS Value (Recommended):** ⭐
```
vCores: 4
RAM:    8 GB
SSD:    160 GB
Price:  ~€12-15/month
```
**Good for:** Production, medium teams (100-500 users)

---

#### **VPS Essential:**
```
vCores: 8
RAM:    16 GB
SSD:    320 GB
Price:  ~€24-30/month
```
**Good for:** Large teams (500-1000 users)

---

### **OVH Additional Services:**

**Backup Service:**
- Automated daily backups
- Cost: ~€2-3/month
- **Recommended:** Yes

**Additional Storage:**
- Block storage for files
- Cost: ~€0.04/GB/month
- **Recommended:** If > 50 GB files

**Anti-DDoS:**
- Usually included
- **Recommended:** Ensure it's enabled

---

## 📋 Pre-Installation Checklist

### **Before Ordering VM:**
- [ ] Choose Ubuntu 22.04 LTS as OS
- [ ] Select appropriate tier (Recommended: VPS Value)
- [ ] Enable backup service
- [ ] Note down root password/SSH key
- [ ] Plan IP address (static recommended)

### **After VM Provisioning:**
- [ ] Update system: `apt update && apt upgrade`
- [ ] Set up non-root user with sudo
- [ ] Configure SSH keys
- [ ] Set up firewall (UFW)
- [ ] Install fail2ban
- [ ] Configure timezone: `timedatectl set-timezone Asia/Kolkata`
- [ ] Set up NTP: `timedatectl set-ntp true`
- [ ] Configure hostname
- [ ] Set up swap space

---

## 🔧 Installation Commands

### **Initial System Setup:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y build-essential git curl wget vim \
    software-properties-common apt-transport-https ca-certificates

# Set timezone
sudo timedatectl set-timezone Asia/Kolkata

# Create swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### **Install Python 3.11:**
```bash
# Add deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Set as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

### **Install PostgreSQL:**
```bash
# Install PostgreSQL 14
sudo apt install -y postgresql-14 postgresql-contrib libpq-dev

# Start and enable
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE hr_assistant;"
sudo -u postgres psql -c "CREATE USER hr_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hr_assistant TO hr_user;"
```

### **Install Nginx:**
```bash
# Install Nginx
sudo apt install -y nginx

# Start and enable
sudo systemctl start nginx
sudo systemctl enable nginx

# Install Certbot for SSL
sudo apt install -y certbot python3-certbot-nginx
```

### **Install Redis (Optional):**
```bash
# Install Redis
sudo apt install -y redis-server

# Configure for production
sudo sed -i 's/supervised no/supervised systemd/' /etc/redis/redis.conf

# Restart
sudo systemctl restart redis
sudo systemctl enable redis
```

### **Install Supervisor:**
```bash
# Install Supervisor
sudo apt install -y supervisor

# Start and enable
sudo systemctl start supervisor
sudo systemctl enable supervisor
```

### **Security Setup:**
```bash
# Install and configure UFW
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Install fail2ban
sudo apt install -y fail2ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# Enable automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📊 Resource Monitoring

### **Commands to Monitor:**
```bash
# CPU usage
htop
top

# Memory usage
free -h
vmstat 1

# Disk usage
df -h
du -sh /var/lib/postgresql
du -sh /var/uploads

# Network
nethogs
iftop

# PostgreSQL
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application
sudo tail -f /var/log/hr-assistant/app.log
```

---

## ✅ Final Recommendations

### **PHASE 1: Internal Team Pilot (10 users)** ⭐ **ORDER THIS NOW**

```yaml
Provider:   OVH VPS Starter
OS:         Ubuntu 22.04 LTS (64-bit)
vCores:     2
RAM:        4 GB
Storage:    40 GB SSD
Backup:     Yes (weekly automated)
Location:   Europe (closest to India with good latency)
Price:      €6-8/month (~₹550-700/month)
```

**Why This Configuration:**
- ✅ **Perfect for 10 internal users**
- ✅ **Cost-effective for pilot phase** (~₹6,600-8,800/year)
- ✅ **Low risk investment** for testing
- ✅ **Quick setup** (2-3 hours)
- ✅ **Easy to upgrade** when ready for white label
- ✅ **Sufficient for 2-3 months** of internal testing

**This configuration will:**
- ✅ Handle 10 concurrent users comfortably
- ✅ Store 10,000+ resumes
- ✅ Process 50 requests/second
- ✅ Provide fast response times (< 500ms)
- ✅ Allow thorough testing and feedback gathering

**Upgrade Path:**
- When team grows > 15 users → Upgrade to VPS Value (€12-15/month)
- When moving to white label → Scale based on client size
- Easy upgrade with minimal downtime

---

### **PHASE 2: White Label Product - Per Client Pricing**

#### **Small Client (20-50 users):**
```yaml
Configuration:  OVH VPS Starter
vCores:        2
RAM:           4 GB
Storage:       60 GB SSD
Price:         €8-12/month
Your Pricing:  ₹2,000-3,000/month per client
```

#### **Medium Client (100-200 users):**
```yaml
Configuration:  OVH VPS Value
vCores:        4
RAM:           8 GB
Storage:       120 GB SSD
Price:         €12-18/month
Your Pricing:  ₹5,000-8,000/month per client
```

#### **Large Client (500+ users):**
```yaml
Configuration:  OVH VPS Essential
vCores:        8
RAM:           16 GB
Storage:       250 GB SSD
Price:         €24-35/month
Your Pricing:  ₹15,000-25,000/month per client
```

---

## 🎯 Summary

### **Phase 1: Internal Team (Current)** ⭐
```
Configuration:  2 vCPUs, 4 GB RAM, 40 GB SSD
Cost:          €6-8/month (~₹550-700/month)
Users:         10 internal team members
Duration:      2-3 months pilot
Purpose:       Testing, feedback, refinement
```

### **Phase 2: White Label (Future)**
```
Configuration:  Varies by client size (2-8 vCPUs)
Cost:          €8-35/month per client
Revenue:       ₹2,000-25,000/month per client
Purpose:       Commercial product offering
Scalability:   Multi-tenant, per-client VMs
```

---

## 💰 Business Model (Phase 2)

### **Revenue Projection:**
```
Small Clients (20-50 users):
- Your Cost: €8-12/month (~₹700-1,100)
- Your Price: ₹2,000-3,000/month
- Margin: 60-70%

Medium Clients (100-200 users):
- Your Cost: €12-18/month (~₹1,100-1,600)
- Your Price: ₹5,000-8,000/month
- Margin: 70-80%

Large Clients (500+ users):
- Your Cost: €24-35/month (~₹2,200-3,200)
- Your Price: ₹15,000-25,000/month
- Margin: 80-85%
```

### **Example: 10 Clients After 1 Year**
```
3 Small Clients:   ₹7,500/month
5 Medium Clients:  ₹32,500/month
2 Large Clients:   ₹40,000/month
────────────────────────────────
Total Revenue:     ₹80,000/month
Total Cost:        ₹15,000/month
Net Profit:        ₹65,000/month
```

---

## 🚀 Action Plan

### **Immediate (This Week):**
1. ✅ Order OVH VPS Starter (2 vCPU, 4 GB RAM, 40 GB SSD)
2. ✅ Set up Ubuntu 22.04 LTS
3. ✅ Deploy application
4. ✅ Invite 10 internal team members

### **Next 2-3 Months:**
1. ✅ Gather feedback from internal team
2. ✅ Refine features based on feedback
3. ✅ Fix bugs and improve UX
4. ✅ Prepare white label version

### **After Internal Pilot:**
1. ✅ Finalize pricing model
2. ✅ Create client onboarding process
3. ✅ Set up automated provisioning
4. ✅ Launch white label product

---

**START HERE: Order OVH VPS Starter for €6-8/month and deploy for internal team!**
