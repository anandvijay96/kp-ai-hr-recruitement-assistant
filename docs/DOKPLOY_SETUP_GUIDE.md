# Dokploy Setup Guide - Step by Step

**📅 Date:** October 13, 2025 - 2:02 PM IST  
**🎯 Status:** Dokploy installed successfully!

---

## ✅ Current Status

- ✅ Dokploy installed
- ✅ User registered and logged in
- ✅ Accessing at: `http://158.69.219.206:3000`

---

## 📋 Step-by-Step Setup

### **Step 1: Create a Project** ⭐ **YOU ARE HERE**

1. Click the **"+ Create Project"** button (top right)
2. Enter project details:
   - **Project Name:** `AI HR Assistant`
   - **Description:** `AI-powered HR recruitment system`
3. Click **"Create"**

**A project is a container that holds your applications, databases, and services.**

---

### **Step 2: Create PostgreSQL Database**

After creating the project:

1. Click on your project **"AI HR Assistant"**
2. You'll see tabs: **Applications**, **Databases**, **Compose**, etc.
3. Click on the **"Databases"** tab
4. Click **"+ Create Database"**
5. Select **"PostgreSQL"**
6. Configure:
   ```
   Name:           hr-postgres
   Database Name:  hr_assistant_db
   Username:       hr_user
   Password:       (generate strong password - save it!)
   Version:        14 or 15
   Port:           5432 (default)
   ```
7. Click **"Create"**

**Save the credentials! You'll need them for the application.**

---

### **Step 3: Create Redis Instance**

Still in your project:

1. Click **"Databases"** tab
2. Click **"+ Create Database"**
3. Select **"Redis"**
4. Configure:
   ```
   Name:     hr-redis
   Version:  7
   Port:     6379 (default)
   Password: (optional - leave empty for internal use)
   ```
5. Click **"Create"**

---

### **Step 4: Create Application**

Now create the main application:

1. Click **"Applications"** tab
2. Click **"+ Create Application"**
3. Choose deployment method:

#### **Option A: GitHub Deployment (Recommended)**
```
Name:           AI HR Assistant
Source:         GitHub
Repository:     (connect your GitHub account first)
Branch:         main
Build Type:     Dockerfile
Port:           8000
```

#### **Option B: Docker Image**
```
Name:           AI HR Assistant
Source:         Docker Image
Image:          (we'll build this locally first)
Port:           8000
```

#### **Option C: Docker Compose**
```
Name:           AI HR Assistant
Source:         Docker Compose
(Upload docker-compose.yml)
```

---

### **Step 5: Configure Environment Variables**

In your application settings:

1. Click on your application
2. Go to **"Environment"** tab
3. Add these variables:
   ```
   DATABASE_URL=postgresql://hr_user:YOUR_PASSWORD@hr-postgres:5432/hr_assistant_db
   REDIS_URL=redis://hr-redis:6379/0
   SECRET_KEY=(generate random string)
   ENVIRONMENT=production
   ALLOWED_HOSTS=158.69.219.206
   ```

**To generate SECRET_KEY:**
```bash
openssl rand -hex 32
```

---

### **Step 6: Configure Domain (Optional - Later)**

1. Go to **"Domains"** tab in your application
2. Click **"+ Add Domain"**
3. Enter your domain: `hr.yourdomain.com`
4. Dokploy will automatically:
   - Configure Traefik reverse proxy
   - Request SSL certificate from Let's Encrypt
   - Set up HTTPS redirect

---

## 🐳 Prepare Your Application for Dokploy

### **Required Files:**

#### **1. Create Dockerfile**

Create `Dockerfile` in your project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run database migrations and start app
CMD alembic upgrade head && \
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

#### **2. Create .dockerignore**

Create `.dockerignore` in your project root:

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
*.db
*.sqlite3
.env
.git/
.gitignore
.idea/
.vscode/
*.log
node_modules/
.DS_Store
```

---

#### **3. Update requirements.txt**

Ensure all dependencies are listed:

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
celery==5.3.4
redis==5.0.1
python-docx==1.1.0
PyPDF2==3.0.1
openpyxl==3.1.2
requests==2.31.0
jinja2==3.1.2
aiofiles==23.2.1
```

---

#### **4. Create Health Check Endpoint**

Add to your `main.py`:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
```

---

#### **5. Update Database Configuration**

Update your database connection to use environment variables:

```python
# config.py or wherever you configure database
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./hr_assistant.db"  # Fallback for local dev
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key")
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 🚀 Deployment Options

### **Option 1: Deploy from GitHub (Easiest)**

1. **Push code to GitHub:**
   ```bash
   cd d:\Projects\BMAD\ai-hr-assistant
   git init
   git add .
   git commit -m "Prepare for Dokploy deployment"
   git branch -M main
   git remote add origin https://github.com/yourusername/ai-hr-assistant.git
   git push -u origin main
   ```

2. **In Dokploy:**
   - Create Application
   - Select "GitHub"
   - Connect GitHub account
   - Select repository
   - Select branch: `main`
   - Build type: Dockerfile
   - Port: 8000
   - Deploy!

---

### **Option 2: Deploy Docker Image (Manual)**

1. **Build image locally:**
   ```bash
   cd d:\Projects\BMAD\ai-hr-assistant
   docker build -t ai-hr-assistant:latest .
   ```

2. **Save and transfer to server:**
   ```bash
   docker save ai-hr-assistant:latest | gzip > ai-hr-assistant.tar.gz
   scp ai-hr-assistant.tar.gz ubuntu@158.69.219.206:/home/ubuntu/
   ```

3. **On server:**
   ```bash
   docker load < ai-hr-assistant.tar.gz
   ```

4. **In Dokploy:**
   - Create Application
   - Select "Docker Image"
   - Image: `ai-hr-assistant:latest`
   - Port: 8000
   - Deploy!

---

### **Option 3: Deploy with Docker Compose**

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**In Dokploy:**
- Create Application
- Select "Docker Compose"
- Upload `docker-compose.yml`
- Set environment variables
- Deploy!

---

## 📊 Dokploy Project Structure

```
Project: AI HR Assistant
├── Databases
│   ├── hr-postgres (PostgreSQL 14)
│   │   └── Connection: hr-postgres:5432
│   └── hr-redis (Redis 7)
│       └── Connection: hr-redis:6379
│
├── Applications
│   └── AI HR Assistant
│       ├── Source: GitHub/Docker
│       ├── Port: 8000
│       ├── Environment Variables
│       ├── Domains
│       └── Logs
│
└── Settings
    ├── Environment Variables
    ├── Domains
    └── Backups
```

---

## 🔍 Monitoring & Logs

### **View Application Logs:**
1. Click on your application
2. Go to **"Logs"** tab
3. Real-time logs will appear

### **View Database Logs:**
1. Click on your database
2. Go to **"Logs"** tab

### **Monitor Resources:**
1. Go to **"Monitoring"** in sidebar
2. View CPU, RAM, Disk usage
3. View per-application metrics

---

## 🔒 Security Checklist

After deployment:

- [ ] Change default Dokploy admin password
- [ ] Set strong PostgreSQL password
- [ ] Generate secure SECRET_KEY
- [ ] Configure firewall (UFW)
- [ ] Set up SSL/HTTPS with domain
- [ ] Enable automatic backups
- [ ] Set up monitoring alerts

---

## 🎯 Quick Reference

### **Database Connection Strings:**

**PostgreSQL (internal):**
```
postgresql://hr_user:YOUR_PASSWORD@hr-postgres:5432/hr_assistant_db
```

**Redis (internal):**
```
redis://hr-redis:6379/0
```

### **Application URL:**

**Without domain:**
```
http://158.69.219.206:8000
```

**With domain (after setup):**
```
https://hr.yourdomain.com
```

---

## 🚀 Next Steps

1. ✅ **Create Project** in Dokploy
2. ✅ **Create PostgreSQL** database
3. ✅ **Create Redis** instance
4. ✅ **Prepare application** (Dockerfile, etc.)
5. ✅ **Deploy application**
6. ✅ **Test and verify**
7. ✅ **Set up domain** (optional)
8. ✅ **Invite internal team**

---

## 💡 Tips

- **Project = Container** for all related services
- **Internal networking** - Services can talk to each other by name
- **No need to expose ports** - Traefik handles routing
- **Automatic SSL** - Just add domain, Dokploy does the rest
- **Zero downtime** - Rolling updates when you redeploy

---

**Ready to create your first project?** Click that "+ Create Project" button! 🚀
