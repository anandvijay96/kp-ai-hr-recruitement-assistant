# 🚀 Deployment Guide

This guide covers deploying the AI HR Assistant to various cloud platforms.

## 📋 Table of Contents
- [Render (Free Tier) - Recommended](#render-deployment)
- [Railway](#railway-deployment)
- [Heroku](#heroku-deployment)
- [Docker](#docker-deployment)

---

## 🎯 Render Deployment (Recommended for MVP)

### Prerequisites
- GitHub account
- Render account (free at [render.com](https://render.com))
- Code pushed to GitHub repository

### Step-by-Step Deployment

#### 1. Prepare Your Repository

Ensure these files are in your repo:
- ✅ `requirements.txt` - Python dependencies
- ✅ `Aptfile` - System dependencies (Tesseract OCR)
- ✅ `render.yaml` - Render configuration (optional but recommended)

#### 2. Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Authorize Render to access your repositories

#### 3. Create New Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure the service:

**Basic Settings:**
```
Name: ai-hr-assistant
Region: Oregon (or closest to you)
Branch: main
Runtime: Python 3
```

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### 4. Add System Dependencies

Render will automatically detect the `Aptfile` and install Tesseract OCR.

If not using `Aptfile`, add this to Build Command:
```bash
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng && pip install -r requirements.txt
```

#### 5. Environment Variables (Optional)

Add these in Render dashboard if needed:
```
PYTHON_VERSION=3.10.0
MAX_FILE_SIZE=10485760
```

#### 6. Deploy

1. Click **"Create Web Service"**
2. Wait 5-10 minutes for initial deployment
3. Your app will be live at: `https://your-app-name.onrender.com`

#### 7. Verify Deployment

Test these endpoints:
- `https://your-app.onrender.com/` - Home page
- `https://your-app.onrender.com/api/health` - Health check
- `https://your-app.onrender.com/upload` - Upload page

### ⚠️ Free Tier Limitations

**Render Free Tier:**
- ✅ 750 hours/month (enough for 24/7 if single app)
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ Cold start takes 30-60 seconds
- ⚠️ 512MB RAM limit
- ⚠️ Shared CPU

**Tips for Free Tier:**
1. **Keep it warm:** Use a service like [UptimeRobot](https://uptimerobot.com/) to ping every 10 minutes
2. **Optimize:** Limit OCR to 3 pages instead of 5 for faster processing
3. **Cache:** Use the built-in caching to reduce processing time

---

## 🚂 Railway Deployment

### Prerequisites
- GitHub account
- Railway account (free at [railway.app](https://railway.app))

### Deployment Steps

#### 1. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository

#### 2. Configure Build

Railway auto-detects Python apps. Add these files:

**`railway.json`:**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

**`nixpacks.toml`:**
```toml
[phases.setup]
aptPkgs = ["tesseract-ocr", "tesseract-ocr-eng"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "uvicorn main:app --host 0.0.0.0 --port $PORT"
```

#### 3. Deploy

1. Railway will auto-deploy on push
2. Get your URL from Railway dashboard
3. Test the deployment

**Railway Free Tier:**
- ✅ $5 free credit/month
- ✅ No cold starts
- ✅ Better performance than Render
- ⚠️ Credit runs out if heavily used

---

## 🐳 Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

# Install system dependencies including Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads results temp

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/health')"

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (for local testing)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./results:/app/results
      - ./temp:/app/temp
    environment:
      - PYTHON_ENV=production
      - MAX_FILE_SIZE=10485760
    restart: unless-stopped
```

### Build and Run

```bash
# Build image
docker build -t ai-hr-assistant .

# Run container
docker run -p 8000:8000 ai-hr-assistant

# Or use docker-compose
docker-compose up -d
```

### Deploy to Cloud

**Docker-based platforms:**
- **Google Cloud Run** - Serverless, pay per use
- **AWS ECS/Fargate** - Scalable container service
- **DigitalOcean App Platform** - Simple deployment
- **Azure Container Instances** - Easy container hosting

---

## 🔧 Post-Deployment Configuration

### 1. Set Up Custom Domain (Optional)

**Render:**
1. Go to Settings → Custom Domains
2. Add your domain
3. Update DNS records as instructed

### 2. Enable HTTPS

All platforms provide automatic HTTPS. No configuration needed!

### 3. Set Up Monitoring

**Recommended Tools:**
- **UptimeRobot** - Free uptime monitoring
- **Sentry** - Error tracking (free tier available)
- **LogTail** - Log management

### 4. Configure CORS (if needed)

Add to `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Performance Optimization for Production

### 1. Reduce OCR Pages

In `services/document_processor.py`:
```python
max_pages = min(3, doc.page_count)  # Reduce from 5 to 3
```

### 2. Add Request Timeout

In `main.py`:
```python
from fastapi import FastAPI
import uvicorn

app = FastAPI(timeout=300)  # 5 minute timeout
```

### 3. Implement Rate Limiting

```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/scan-resume")
@limiter.limit("10/minute")
async def scan_resume(...):
    ...
```

---

## 🐛 Troubleshooting

### Issue: Tesseract Not Found

**Solution:**
Ensure `Aptfile` is in root directory with:
```
tesseract-ocr
tesseract-ocr-eng
```

Or add to build command:
```bash
apt-get install -y tesseract-ocr
```

### Issue: Out of Memory

**Solution:**
- Reduce OCR page limit
- Upgrade to paid tier
- Implement file size limits

### Issue: Cold Starts (Render)

**Solution:**
- Use UptimeRobot to ping every 10 minutes
- Upgrade to paid tier ($7/month)
- Switch to Railway (no cold starts)

### Issue: Slow Performance

**Solution:**
- Enable caching (already implemented)
- Reduce batch size limit
- Optimize OCR resolution
- Use CDN for static files

---

## 💰 Cost Comparison

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| **Render** | 750 hrs/mo | $7/mo | MVP/Testing |
| **Railway** | $5 credit/mo | $5/mo+ | Small projects |
| **Heroku** | None | $7/mo | Production |
| **DigitalOcean** | None | $5/mo | Full control |
| **AWS/GCP** | Free tier | Pay-as-go | Scalability |

---

## ✅ Deployment Checklist

Before deploying:

- [ ] All tests passing
- [ ] Requirements.txt updated
- [ ] Environment variables documented
- [ ] Aptfile created (for Tesseract)
- [ ] README.md updated with deployment URL
- [ ] Health check endpoint working
- [ ] Error handling tested
- [ ] File upload limits configured
- [ ] CORS configured (if needed)
- [ ] Monitoring set up

---

## 🎉 Your App is Live!

Once deployed, share your app:
- **Live URL:** `https://your-app.onrender.com`
- **API Docs:** `https://your-app.onrender.com/docs`
- **Health Check:** `https://your-app.onrender.com/api/health`

**Next Steps:**
1. Test all features on production
2. Set up monitoring
3. Share with users
4. Collect feedback
5. Iterate and improve!

---

## 📞 Support

If you encounter issues:
1. Check Render/Railway logs
2. Review error messages
3. Test locally with same configuration
4. Check GitHub Issues
5. Contact platform support

**Happy Deploying! 🚀**
