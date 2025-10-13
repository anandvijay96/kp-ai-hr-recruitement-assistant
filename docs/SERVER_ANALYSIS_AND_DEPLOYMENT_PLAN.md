# Server Analysis & Deployment Plan

**📅 Date:** October 13, 2025 - 1:40 PM IST  
**🎯 Server:** OVH VPS (vps-fa3d7ce9)

---

## ✅ Server Specifications - ANALYSIS

### **Your Actual Server (EXCELLENT!):**

```yaml
OS:           Ubuntu 25.04 "Plucky Puffin" ✅
Architecture: x86_64 (64-bit) ✅
CPU:          8 vCPUs (Intel Haswell) ✅✅✅
RAM:          22 GB ✅✅✅
Storage:      193 GB SSD ✅✅
Swap:         0 GB (needs to be created)
Python:       3.13.3 ✅
IP:           158.69.219.206 (IPv4)
              2607:5300:205:200::4a3e (IPv6)
Hostname:     vps-fa3d7ce9
User:         ubuntu (with sudo access) ✅
Internet:     Active (0% packet loss) ✅
```

---

## 🎉 **WOW! This Server is POWERFUL!**

### **What We Expected:**
- 2 vCPUs, 4 GB RAM, 40 GB Storage

### **What You Actually Have:**
- **8 vCPUs** (4x more!)
- **22 GB RAM** (5.5x more!)
- **193 GB Storage** (4.8x more!)

**This server can easily host 5-10 applications simultaneously!**

---

## 🚀 Recommended Approach: **Dokploy** (Better for Your Use Case)

### **Why Dokploy over Coolify:**

#### **Dokploy Advantages:**
- ✅ **Lighter weight** - Less resource overhead
- ✅ **Simpler UI** - Easier to learn and use
- ✅ **Docker-based** - Modern containerization
- ✅ **Built-in PostgreSQL** - Perfect for our app
- ✅ **Traefik integration** - Automatic SSL/HTTPS
- ✅ **Git deployment** - Deploy from GitHub/GitLab
- ✅ **Environment variables** - Easy configuration
- ✅ **Better for 5-10 apps** - Optimized for medium scale
- ✅ **Active development** - Regular updates

#### **Coolify Advantages:**
- ✅ **More features** - But also more complex
- ✅ **Better for 20+ apps** - Overkill for your needs
- ✅ **More resource intensive** - Uses more RAM/CPU

**Recommendation: Use Dokploy** ⭐

---

## 📋 Deployment Architecture with Dokploy

### **Server Resource Allocation:**

```
Total Resources:
- 8 vCPUs
- 22 GB RAM
- 193 GB Storage

Allocation Plan:
┌─────────────────────────────────────────┐
│ Dokploy (Control Panel)                │
│ - 1 vCPU, 2 GB RAM, 10 GB Storage      │
├─────────────────────────────────────────┤
│ AI HR Assistant (Your App)             │
│ - 2 vCPUs, 6 GB RAM, 60 GB Storage     │
├─────────────────────────────────────────┤
│ PostgreSQL (Shared Database)           │
│ - 1 vCPU, 4 GB RAM, 40 GB Storage      │
├─────────────────────────────────────────┤
│ Redis (Caching/Sessions)               │
│ - 1 vCPU, 2 GB RAM, 5 GB Storage       │
├─────────────────────────────────────────┤
│ Future Apps (3-4 more apps)            │
│ - 3 vCPUs, 8 GB RAM, 60 GB Storage     │
├─────────────────────────────────────────┤
│ System & Buffer                        │
│ - Reserved: 2 GB RAM, 18 GB Storage    │
└─────────────────────────────────────────┘
```

---

## 🎯 Deployment Plan

### **Phase 1: Install Dokploy (30 minutes)**

#### **Step 1: Create Swap Space**
```bash
# Create 4 GB swap (recommended for 22 GB RAM)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Optimize swappiness
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Verify
free -h
```

#### **Step 2: Update System**
```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget git vim htop
```

#### **Step 3: Install Docker**
```bash
# Install Docker (required for Dokploy)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Start Docker
sudo systemctl enable docker
sudo systemctl start docker

# Verify
docker --version
```

#### **Step 4: Install Dokploy**
```bash
# Install Dokploy (one command!)
curl -sSL https://dokploy.com/install.sh | sh

# This will:
# - Install Dokploy
# - Set up Traefik (reverse proxy)
# - Configure SSL/HTTPS
# - Start the web interface
```

**After installation, Dokploy will be available at:**
- **URL:** `http://158.69.219.206:3000`
- **Default credentials:** Will be shown after installation

---

### **Phase 2: Configure Dokploy (15 minutes)**

#### **Step 1: Access Dokploy**
1. Open browser: `http://158.69.219.206:3000`
2. Login with credentials from installation
3. Change default password

#### **Step 2: Set Up Domain (Optional but Recommended)**
If you have a domain (e.g., `hr.yourdomain.com`):
1. Point domain A record to: `158.69.219.206`
2. In Dokploy: Settings → Domains → Add domain
3. Dokploy will auto-configure SSL with Let's Encrypt

#### **Step 3: Create PostgreSQL Database**
1. In Dokploy: Databases → Create Database
2. Type: PostgreSQL 14
3. Name: `hr_assistant_db`
4. Username: `hr_user`
5. Password: (generate strong password)
6. Save credentials

#### **Step 4: Create Redis Instance (Optional)**
1. In Dokploy: Databases → Create Database
2. Type: Redis
3. Name: `hr_assistant_redis`
4. No password needed for internal use

---

### **Phase 3: Deploy AI HR Assistant (30 minutes)**

#### **Option A: Deploy from GitHub (Recommended)**

**Step 1: Push Code to GitHub**
```bash
# On your local machine
cd d:\Projects\BMAD\ai-hr-assistant
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/ai-hr-assistant.git
git push -u origin main
```

**Step 2: Create Dockerfile**
Create `Dockerfile` in project root:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 3: Create docker-compose.yml** (for Dokploy)
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://hr_user:${DB_PASSWORD}@postgres:5432/hr_assistant_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=hr_assistant_db
      - POSTGRES_USER=hr_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

**Step 4: Deploy in Dokploy**
1. In Dokploy: Applications → Create Application
2. Name: `AI HR Assistant`
3. Source: GitHub
4. Repository: `https://github.com/yourusername/ai-hr-assistant`
5. Branch: `main`
6. Build Type: Docker Compose
7. Environment Variables:
   - `DB_PASSWORD`: (your PostgreSQL password)
   - `SECRET_KEY`: (generate random string)
8. Domain: `hr.yourdomain.com` (or use IP)
9. Click Deploy

**Dokploy will automatically:**
- ✅ Clone repository
- ✅ Build Docker image
- ✅ Start containers
- ✅ Configure reverse proxy
- ✅ Set up SSL/HTTPS
- ✅ Monitor application

---

#### **Option B: Manual Docker Deployment**

If you prefer manual control:

```bash
# 1. Clone repository on server
cd /home/ubuntu
git clone https://github.com/yourusername/ai-hr-assistant.git
cd ai-hr-assistant

# 2. Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://hr_user:your_password@localhost:5432/hr_assistant_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=production
EOF

# 3. Build and run with Docker Compose
docker-compose up -d

# 4. Check logs
docker-compose logs -f
```

---

## 🔒 Security Configuration

### **Step 1: Configure Firewall**
```bash
# Install UFW
sudo apt install -y ufw

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow Dokploy
sudo ufw allow 3000/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### **Step 2: Install Fail2ban**
```bash
# Install fail2ban
sudo apt install -y fail2ban

# Start and enable
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

### **Step 3: Set Up SSH Key Authentication**
```bash
# On your local machine, generate SSH key (if not already)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy to server
ssh-copy-id ubuntu@158.69.219.206

# On server, disable password authentication
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
# Set: PermitRootLogin no

# Restart SSH
sudo systemctl restart sshd
```

---

## 📊 Resource Monitoring

### **Monitor with Dokploy Dashboard:**
- CPU usage per app
- Memory usage per app
- Disk usage
- Network traffic
- Application logs

### **Command Line Monitoring:**
```bash
# Overall system
htop

# Docker containers
docker stats

# Disk usage
df -h

# Memory
free -h

# Network
nethogs
```

---

## 🎯 Multi-App Hosting Plan

### **Current Capacity:**
With 8 vCPUs and 22 GB RAM, you can host:

```
1. AI HR Assistant (Production)
   - 2 vCPUs, 6 GB RAM
   
2. AI HR Assistant (Staging/Testing)
   - 1 vCPU, 2 GB RAM
   
3. Future App #1
   - 1 vCPU, 3 GB RAM
   
4. Future App #2
   - 1 vCPU, 3 GB RAM
   
5. Future App #3
   - 1 vCPU, 3 GB RAM
   
6. Shared Services
   - PostgreSQL: 1 vCPU, 4 GB RAM
   - Redis: 1 vCPU, 1 GB RAM
   - Dokploy: Reserved resources
```

**Total: 5-6 applications comfortably!**

---

## 🚀 Deployment Timeline

### **Today (2-3 hours):**
1. ✅ Install Dokploy (30 min)
2. ✅ Configure Dokploy (15 min)
3. ✅ Prepare application for Docker (30 min)
4. ✅ Deploy AI HR Assistant (30 min)
5. ✅ Configure security (30 min)
6. ✅ Test and verify (30 min)

### **This Week:**
1. ✅ Set up domain and SSL
2. ✅ Configure backups
3. ✅ Set up monitoring alerts
4. ✅ Invite internal team (10 users)

---

## 💡 Advantages of This Setup

### **With Dokploy:**
- ✅ **Easy deployment** - Git push to deploy
- ✅ **Zero downtime** - Rolling updates
- ✅ **Automatic SSL** - Let's Encrypt integration
- ✅ **Environment management** - Dev/Staging/Prod
- ✅ **Scalability** - Easy to add more apps
- ✅ **Monitoring** - Built-in dashboards
- ✅ **Backups** - Automated database backups
- ✅ **Rollbacks** - One-click rollback to previous version

### **Resource Efficiency:**
- ✅ **Containerization** - Isolated apps
- ✅ **Shared database** - Reduce overhead
- ✅ **Shared Redis** - Centralized caching
- ✅ **Reverse proxy** - Single entry point
- ✅ **Resource limits** - Prevent one app from hogging resources

---

## 📋 Next Steps

### **Immediate Actions:**

1. **Install Dokploy** (30 min)
   ```bash
   curl -sSL https://dokploy.com/install.sh | sh
   ```

2. **Create Swap** (5 min)
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

3. **Access Dokploy**
   - URL: `http://158.69.219.206:3000`
   - Set up admin account

4. **Prepare Application**
   - Create Dockerfile
   - Create docker-compose.yml
   - Push to GitHub

5. **Deploy!**
   - Connect GitHub in Dokploy
   - Deploy application
   - Test and verify

---

## 🎯 Decision Time

**Do you want to:**

### **Option 1: Use Dokploy (Recommended)** ⭐
- Modern, easy to use
- Perfect for 5-10 apps
- Great UI and monitoring
- I'll create step-by-step guide

### **Option 2: Manual Docker Setup**
- More control
- Steeper learning curve
- Good for learning Docker
- I'll create deployment scripts

### **Option 3: Traditional Setup (No Docker)**
- Direct installation on server
- Simpler initially
- Harder to scale later
- I'll create installation guide

---

**Which option do you prefer? Then we'll proceed with deployment and get back to P0 features!** 🚀
