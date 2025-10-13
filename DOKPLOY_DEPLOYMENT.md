# Dokploy Deployment Guide - MVP-1 Branch

**📅 Date:** October 13, 2025  
**🎯 Branch:** mvp-1 (separate from Railway's main branch)  
**🚀 Platform:** Dokploy on OVH VPS

---

## ✅ Prerequisites Completed

- ✅ Dokploy installed on server (158.69.219.206:3000)
- ✅ User registered and logged in
- ✅ Server specs: 8 vCPUs, 22 GB RAM, 193 GB Storage
- ✅ Docker files created (Dockerfile, .dockerignore, docker-compose.yml)

---

## 📋 Step 1: Commit and Push to mvp-1 Branch

### **On Your Local Machine:**

```bash
# Navigate to project directory
cd d:\Projects\BMAD\ai-hr-assistant

# Check current branch
git branch

# If not on mvp-1, create and switch to it
git checkout -b mvp-1

# Stage all changes
git add .

# Commit changes
git commit -m "Add Docker configuration for Dokploy deployment

- Updated Dockerfile with Python 3.11 and production settings
- Added PostgreSQL and Redis support
- Configured health checks and multi-worker setup
- Added docker-compose.yml for local testing
- Ready for Dokploy deployment on mvp-1 branch"

# Push to remote mvp-1 branch
git push origin mvp-1

# If this is the first push to mvp-1:
git push -u origin mvp-1
```

---

## 📋 Step 2: Create Project in Dokploy

1. **Access Dokploy:** `http://158.69.219.206:3000`
2. **Click:** "+ Create Project" (top right)
3. **Enter:**
   - **Name:** `AI HR Assistant`
   - **Description:** `AI-powered HR recruitment system - MVP-1`
4. **Click:** "Create"

---

## 📋 Step 3: Create PostgreSQL Database

1. **Click** on your project "AI HR Assistant"
2. **Go to** "Databases" tab
3. **Click** "+ Create Database"
4. **Select** "PostgreSQL"
5. **Configure:**
   ```
   Name:           hr-postgres
   Database Name:  hr_assistant_db
   Username:       hr_user
   Password:       [Generate strong password - SAVE IT!]
   Version:        14 or 15
   Port:           5432
   ```
6. **Click** "Create"

**⚠️ IMPORTANT: Save the password! You'll need it for environment variables.**

---

## 📋 Step 4: Create Redis Instance

1. **Still in** "Databases" tab
2. **Click** "+ Create Database"
3. **Select** "Redis"
4. **Configure:**
   ```
   Name:     hr-redis
   Version:  7
   Port:     6379
   ```
5. **Click** "Create"

---

## 📋 Step 5: Create Application

1. **Go to** "Applications" tab
2. **Click** "+ Create Application"
3. **Select** "GitHub" as source
4. **Connect GitHub** (if not already connected)
5. **Configure:**
   ```
   Name:           AI HR Assistant
   Repository:     [Your GitHub repo]
   Branch:         mvp-1  ← IMPORTANT: Use mvp-1, not main!
   Build Type:     Dockerfile
   Port:           8000
   ```

---

## 📋 Step 6: Configure Environment Variables

In your application settings, go to "Environment" tab and add:

### **Required Variables:**

```bash
# Database (use the password you saved from Step 3)
DATABASE_URL=postgresql+asyncpg://hr_user:YOUR_PASSWORD_HERE@hr-postgres:5432/hr_assistant_db

# Redis
REDIS_URL=redis://hr-redis:6379/0

# JWT Secret (generate new one)
JWT_SECRET_KEY=<generate-with-command-below>

# Application
ENVIRONMENT=production
APP_NAME=AI Powered HR Assistant
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Frontend URL (use your server IP or domain)
FRONTEND_URL=http://158.69.219.206

# Email (optional for now)
SENDGRID_API_KEY=
SENDER_EMAIL=noreply@hrrecruitment.com
SENDER_NAME=HR Recruitment System
```

### **Generate JWT Secret Key:**

Run this on your local machine or server:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and use it as `JWT_SECRET_KEY`

---

## 📋 Step 7: Deploy Application

1. **Click** "Deploy" button
2. **Wait** for build to complete (5-10 minutes first time)
3. **Monitor** logs in real-time

### **Deployment Process:**
```
1. Clone repository (mvp-1 branch)
2. Build Docker image
3. Start containers
4. Run health checks
5. Configure Traefik routing
6. Application ready!
```

---

## 📋 Step 8: Access Your Application

### **Without Domain:**
```
http://158.69.219.206:8000
```

### **Check Health:**
```
http://158.69.219.206:8000/api/health
```

### **Login Page:**
```
http://158.69.219.206:8000/auth/login
```

---

## 📋 Step 9: Set Up Domain (Optional - Later)

1. **Point your domain** A record to: `158.69.219.206`
2. **In Dokploy** application settings:
   - Go to "Domains" tab
   - Click "+ Add Domain"
   - Enter: `hr.yourdomain.com`
3. **Dokploy will automatically:**
   - Configure Traefik reverse proxy
   - Request SSL certificate from Let's Encrypt
   - Set up HTTPS redirect

---

## 🔍 Monitoring & Troubleshooting

### **View Application Logs:**
1. Click on your application
2. Go to "Logs" tab
3. Real-time logs will appear

### **View Database Logs:**
1. Click on "hr-postgres" database
2. Go to "Logs" tab

### **Common Issues:**

#### **Issue: Build fails**
- Check Dockerfile syntax
- Verify requirements.txt has all dependencies
- Check logs for specific error

#### **Issue: Application won't start**
- Verify environment variables are set correctly
- Check DATABASE_URL format
- Ensure PostgreSQL is running

#### **Issue: Can't connect to database**
- Verify database name matches in DATABASE_URL
- Check PostgreSQL password
- Ensure database is running (check Databases tab)

#### **Issue: Health check fails**
- Wait 40 seconds (start period)
- Check if port 8000 is correct
- Verify /api/health endpoint exists

---

## 🔄 Updating Your Application

### **Method 1: Git Push (Recommended)**
```bash
# Make changes locally
git add .
git commit -m "Your changes"
git push origin mvp-1

# In Dokploy: Click "Redeploy" button
# Dokploy will automatically pull latest code and rebuild
```

### **Method 2: Manual Redeploy**
1. Go to your application in Dokploy
2. Click "Redeploy" button
3. Wait for build to complete

---

## 🗄️ Database Management

### **Connect to PostgreSQL:**

**From server:**
```bash
docker exec -it <postgres-container-id> psql -U hr_user -d hr_assistant_db
```

**From local machine:**
```bash
psql -h 158.69.219.206 -U hr_user -d hr_assistant_db
```

### **Backup Database:**

**In Dokploy:**
1. Go to "hr-postgres" database
2. Click "Backup" button
3. Download backup file

**Manual backup:**
```bash
docker exec <postgres-container-id> pg_dump -U hr_user hr_assistant_db > backup.sql
```

---

## 📊 Resource Usage

### **Expected Usage (10 internal users):**
```
Application:  1-2 vCPUs, 2-4 GB RAM
PostgreSQL:   0.5 vCPU, 1-2 GB RAM
Redis:        0.5 vCPU, 512 MB RAM
Dokploy:      0.5 vCPU, 1 GB RAM
───────────────────────────────────
Total:        2.5-3.5 vCPUs, 4.5-7.5 GB RAM
Available:    8 vCPUs, 22 GB RAM
Headroom:     5.5 vCPUs, 15 GB RAM (plenty!)
```

---

## 🔒 Security Checklist

After deployment:

- [ ] Change default Dokploy admin password
- [ ] Use strong PostgreSQL password
- [ ] Generate secure JWT_SECRET_KEY
- [ ] Set up firewall (UFW) - already done
- [ ] Configure fail2ban - already done
- [ ] Set up SSL/HTTPS with domain (later)
- [ ] Enable automatic backups
- [ ] Set up monitoring alerts

---

## 🎯 Testing Checklist

After deployment:

- [ ] Access application at http://158.69.219.206:8000
- [ ] Health check returns "healthy"
- [ ] Login page loads
- [ ] Can create admin user
- [ ] Can login successfully
- [ ] Dashboard loads
- [ ] Can upload resume
- [ ] Can create job posting
- [ ] Database is persisting data
- [ ] Logs are accessible

---

## 📞 Quick Reference

### **Server Details:**
```
IP:           158.69.219.206
Dokploy:      http://158.69.219.206:3000
Application:  http://158.69.219.206:8000
SSH:          ssh ubuntu@158.69.219.206
```

### **Database Connection:**
```
Host:     hr-postgres (internal) or 158.69.219.206 (external)
Port:     5432
Database: hr_assistant_db
User:     hr_user
Password: [Your saved password]
```

### **Redis Connection:**
```
Host:     hr-redis (internal) or 158.69.219.206 (external)
Port:     6379
```

---

## 🚀 Next Steps After Deployment

1. ✅ **Test application** thoroughly
2. ✅ **Invite internal team** (10 users)
3. ✅ **Gather feedback** for 2-3 months
4. ✅ **Refine features** based on feedback
5. ✅ **Set up domain** and SSL
6. ✅ **Configure automated backups**
7. ✅ **Plan white label** version

---

## 💡 Tips

- **Separate branches:** Keep `main` for Railway, `mvp-1` for Dokploy
- **Environment variables:** Never commit secrets to git
- **Logs:** Check logs first when troubleshooting
- **Health checks:** Give 40 seconds for app to start
- **Backups:** Set up automated daily backups
- **Monitoring:** Check Dokploy dashboard regularly

---

**Ready to deploy? Follow the steps above!** 🚀

---

## 📝 Deployment Log Template

Use this to track your deployment:

```
Date: __________
Branch: mvp-1
Commit: __________

✅ Step 1: Code committed and pushed
✅ Step 2: Project created in Dokploy
✅ Step 3: PostgreSQL created (Password saved: ☐)
✅ Step 4: Redis created
✅ Step 5: Application created
✅ Step 6: Environment variables configured
✅ Step 7: Application deployed
✅ Step 8: Application accessible
✅ Step 9: Testing completed

Notes:
_________________________________
_________________________________
_________________________________
```
