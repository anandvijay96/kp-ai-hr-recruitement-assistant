# Git Commands for MVP-1 Branch Deployment

**📅 Date:** October 13, 2025  
**🎯 Purpose:** Commit changes and push to mvp-1 branch for Dokploy

---

## 🚀 Quick Start Commands

### **Step 1: Check Current Status**
```bash
cd d:\Projects\BMAD\ai-hr-assistant
git status
git branch
```

---

### **Step 2: Create/Switch to mvp-1 Branch**

**If mvp-1 doesn't exist:**
```bash
git checkout -b mvp-1
```

**If mvp-1 already exists:**
```bash
git checkout mvp-1
```

---

### **Step 3: Stage All Changes**
```bash
git add .
```

**Or stage specific files:**
```bash
git add Dockerfile
git add docker-compose.yml
git add .dockerignore
git add DOKPLOY_DEPLOYMENT.md
git add GIT_COMMANDS.md
```

---

### **Step 4: Commit Changes**
```bash
git commit -m "Add Docker configuration for Dokploy deployment

- Updated Dockerfile with Python 3.11 and production settings
- Added PostgreSQL and Redis support in docker-compose.yml
- Configured health checks and multi-worker setup
- Added comprehensive deployment documentation
- Ready for Dokploy deployment on mvp-1 branch
- Keeps main branch separate for Railway deployment"
```

---

### **Step 5: Push to Remote**

**First time pushing mvp-1:**
```bash
git push -u origin mvp-1
```

**Subsequent pushes:**
```bash
git push origin mvp-1
```

---

## 🔄 Future Updates

### **When you make changes:**

```bash
# 1. Make sure you're on mvp-1 branch
git checkout mvp-1

# 2. Pull latest changes (if working with team)
git pull origin mvp-1

# 3. Make your changes to files...

# 4. Stage changes
git add .

# 5. Commit with descriptive message
git commit -m "Your descriptive commit message"

# 6. Push to remote
git push origin mvp-1
```

---

## 🔍 Useful Git Commands

### **Check which branch you're on:**
```bash
git branch
# * mvp-1  ← asterisk shows current branch
#   main
```

### **See what files changed:**
```bash
git status
```

### **See what changed in files:**
```bash
git diff
```

### **View commit history:**
```bash
git log --oneline
```

### **Switch between branches:**
```bash
# Switch to main (Railway)
git checkout main

# Switch to mvp-1 (Dokploy)
git checkout mvp-1
```

### **See all branches (local and remote):**
```bash
git branch -a
```

---

## ⚠️ Important Notes

### **Keep Branches Separate:**
- **main branch** → Railway deployment (don't touch)
- **mvp-1 branch** → Dokploy deployment (work here)

### **Before Pushing:**
1. ✅ Make sure you're on mvp-1 branch
2. ✅ Test locally if possible
3. ✅ Write clear commit message
4. ✅ Don't commit sensitive data (.env files)

### **Files to NEVER Commit:**
- `.env` (contains secrets)
- `*.db` (database files)
- `uploads/` (user uploaded files)
- `__pycache__/` (Python cache)
- `.vscode/`, `.idea/` (IDE settings)

These are already in `.gitignore`, but double-check!

---

## 🎯 Complete Workflow

```bash
# 1. Navigate to project
cd d:\Projects\BMAD\ai-hr-assistant

# 2. Switch to mvp-1 branch
git checkout mvp-1

# 3. Check status
git status

# 4. Stage all changes
git add .

# 5. Commit with message
git commit -m "Add Docker configuration for Dokploy deployment

- Updated Dockerfile with Python 3.11 and production settings
- Added PostgreSQL and Redis support
- Configured health checks and multi-worker setup
- Added deployment documentation
- Ready for Dokploy deployment"

# 6. Push to remote
git push origin mvp-1

# 7. Verify push
git log --oneline -5
```

---

## 🔧 Troubleshooting

### **Problem: "fatal: not a git repository"**
```bash
# Initialize git (if needed)
git init
git remote add origin https://github.com/yourusername/ai-hr-assistant.git
```

### **Problem: "Updates were rejected"**
```bash
# Pull latest changes first
git pull origin mvp-1

# Then push again
git push origin mvp-1
```

### **Problem: "Merge conflict"**
```bash
# See conflicting files
git status

# Edit files to resolve conflicts
# Look for <<<<<<< HEAD markers

# After resolving:
git add .
git commit -m "Resolve merge conflicts"
git push origin mvp-1
```

### **Problem: Accidentally committed to wrong branch**
```bash
# If not pushed yet:
git reset --soft HEAD~1  # Undo last commit, keep changes
git checkout mvp-1       # Switch to correct branch
git add .
git commit -m "Your message"
git push origin mvp-1
```

---

## 📝 Commit Message Best Practices

### **Good commit messages:**
```bash
git commit -m "Add Docker configuration for Dokploy deployment"
git commit -m "Fix: Database connection timeout issue"
git commit -m "Update: Increase health check timeout to 40s"
git commit -m "Feature: Add user authentication endpoint"
```

### **Bad commit messages:**
```bash
git commit -m "fix"
git commit -m "update"
git commit -m "changes"
git commit -m "asdf"
```

---

## ✅ Pre-Push Checklist

Before pushing to mvp-1:

- [ ] On correct branch (mvp-1)
- [ ] All files staged (`git status`)
- [ ] Clear commit message
- [ ] No .env or secrets committed
- [ ] Tested locally (if possible)
- [ ] Ready for Dokploy to pull

---

## 🚀 After Pushing

1. **Go to Dokploy:** http://158.69.219.206:3000
2. **Navigate to** your application
3. **Click** "Redeploy" button
4. **Wait** for build to complete
5. **Check** logs for any errors
6. **Test** application

---

**Ready to commit and push? Run the commands above!** 🚀
