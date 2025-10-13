# Admin User Creation Guide

**📅 Created:** October 13, 2025 - 11:55 PM IST  
**🎯 Purpose:** Create admin users for production environment  
**⚠️ Priority:** URGENT - Required for user management

---

## 🚨 **PROBLEM**

When users register through the signup page, they are assigned the "Recruiter" role by default. There is currently no UI-based way to create admin users or promote existing users to admin.

**Impact:**
- Cannot access admin features
- Cannot manage other users
- Cannot change user roles
- Cannot access system settings

---

## ✅ **SOLUTION**

Two Python scripts have been created to solve this issue:

### **Option 1: Promote Existing User to Admin** ⭐ RECOMMENDED
**Script:** `make_user_admin.py`

**Use Case:** You already have an account and want to make it admin

**Usage:**
```bash
# Local development
python make_user_admin.py your@email.com

# Production (Dokploy)
docker exec -it <container_name> python make_user_admin.py your@email.com
```

**What it does:**
- Finds user by email
- Updates role to "admin"
- Sets status to "active"
- Activates account
- Verifies email

---

### **Option 2: Create New Admin User**
**Script:** `create_production_admin.py`

**Use Case:** You want to create a brand new admin account

**Usage:**
```bash
# Interactive mode
python create_production_admin.py

# Command line mode
python create_production_admin.py admin@company.com SecurePass123! "Admin Name"

# Production (Dokploy)
docker exec -it <container_name> python create_production_admin.py admin@company.com SecurePass123!
```

**What it does:**
- Creates new user with admin role
- Sets secure password
- Activates account immediately
- Verifies email automatically

---

## 🚀 **STEP-BY-STEP INSTRUCTIONS**

### **For Local Development:**

1. **Open terminal in project directory**
   ```bash
   cd d:\Projects\BMAD\ai-hr-assistant
   ```

2. **Run the script**
   ```bash
   # Option 1: Promote your existing account
   python make_user_admin.py your@email.com
   
   # Option 2: Create new admin
   python create_production_admin.py admin@company.com SecurePass123!
   ```

3. **Verify success**
   - You should see: ✅ User promoted to admin successfully!
   - Login with your email and password
   - Check that you can access admin features

---

### **For Production (Dokploy):**

#### **Method 1: Using Dokploy Console** ⭐ EASIEST

1. **Go to Dokploy dashboard**
   - Navigate to your application
   - Click on "Console" or "Terminal" tab

2. **Run the command**
   ```bash
   python make_user_admin.py your@email.com
   ```

3. **Verify**
   - Login to the application
   - Check admin access

---

#### **Method 2: Using Docker Exec**

1. **Find container name**
   ```bash
   docker ps | grep ai-hr-assistant
   ```

2. **Execute script in container**
   ```bash
   docker exec -it <container_name> python make_user_admin.py your@email.com
   ```

3. **Verify**
   - Login to the application
   - Check admin access

---

#### **Method 3: Using SSH**

1. **SSH into server**
   ```bash
   ssh user@158.69.219.206
   ```

2. **Find container**
   ```bash
   docker ps | grep ai-hr-assistant
   ```

3. **Execute script**
   ```bash
   docker exec -it <container_name> python make_user_admin.py your@email.com
   ```

---

## 📋 **SCRIPT DETAILS**

### **make_user_admin.py**

**Location:** `d:\Projects\BMAD\ai-hr-assistant\make_user_admin.py`

**Code Overview:**
```python
async def make_user_admin(email: str):
    """Promote existing user to admin role"""
    # Find user by email
    # Update role to "admin"
    # Set status to "active"
    # Activate account
    # Commit changes
```

**Output:**
```
============================================================
✅ User promoted to admin successfully!
============================================================

User Details:
  Name: John Doe
  Email: john@company.com
  Role: admin
  Status: active
============================================================
```

---

### **create_production_admin.py**

**Location:** `d:\Projects\BMAD\ai-hr-assistant\create_production_admin.py`

**Code Overview:**
```python
async def create_admin_user(email: str, password: str, full_name: str):
    """Create new admin user"""
    # Check if user exists (update if exists)
    # Hash password
    # Create user with admin role
    # Activate and verify
    # Commit changes
```

**Output:**
```
============================================================
✅ Admin user created successfully!
============================================================

Login Credentials:
  Email: admin@company.com
  Password: SecurePass123!
  Role: admin

⚠️  IMPORTANT: Change this password after first login!
============================================================
```

---

## 🔒 **SECURITY CONSIDERATIONS**

### **Password Requirements:**
- Minimum 8 characters
- Include uppercase and lowercase
- Include numbers
- Include special characters
- Example: `SecurePass123!`

### **Best Practices:**
1. ✅ Use strong, unique passwords
2. ✅ Change default passwords immediately after first login
3. ✅ Don't share admin credentials
4. ✅ Use different passwords for different environments
5. ✅ Enable 2FA when available (future feature)

### **Production Security:**
1. ✅ Don't hardcode passwords in scripts
2. ✅ Use environment variables for sensitive data
3. ✅ Rotate admin passwords regularly
4. ✅ Audit admin access logs
5. ✅ Limit number of admin accounts

---

## 🐛 **TROUBLESHOOTING**

### **Issue 1: "User not found"**
**Cause:** Email doesn't exist in database

**Solution:**
- Check email spelling
- Verify user has registered
- Use `create_production_admin.py` to create new user

---

### **Issue 2: "Module not found" error**
**Cause:** Script not in correct directory or dependencies missing

**Solution:**
```bash
# Ensure you're in project directory
cd d:\Projects\BMAD\ai-hr-assistant

# Verify Python environment
python --version

# Check dependencies
pip install -r requirements.txt
```

---

### **Issue 3: "Database locked" error**
**Cause:** Another process is using the database

**Solution:**
- Stop the application
- Run the script
- Restart the application

---

### **Issue 4: "Permission denied" in Docker**
**Cause:** Insufficient permissions

**Solution:**
```bash
# Use sudo if needed
sudo docker exec -it <container_name> python make_user_admin.py email@example.com
```

---

## ✅ **VERIFICATION CHECKLIST**

After creating/promoting admin user:

- [ ] Can login with email and password
- [ ] Can access dashboard
- [ ] Can see "Users" menu item in navigation
- [ ] Can access `/users` page
- [ ] Can view list of users
- [ ] Can create new users
- [ ] Can change user roles
- [ ] Can deactivate users
- [ ] Can access system settings
- [ ] Can view audit logs

---

## 🔄 **FUTURE IMPROVEMENTS**

### **Planned Features:**
1. **UI-based Admin Creation**
   - Add admin creation form in settings
   - Require super-admin permission
   - Email verification flow

2. **Role Management UI**
   - Promote/demote users from UI
   - Bulk role changes
   - Role-based permissions matrix

3. **Self-Service Admin Request**
   - Users can request admin access
   - Approval workflow
   - Notification system

4. **Multi-Factor Authentication**
   - 2FA for admin accounts
   - SMS/Email verification
   - Authenticator app support

---

## 📞 **SUPPORT**

### **If Scripts Don't Work:**

1. **Check logs:**
   ```bash
   # Local
   python make_user_admin.py your@email.com 2>&1 | tee admin_creation.log
   
   # Production
   docker logs <container_name> | grep admin
   ```

2. **Manual database update (last resort):**
   ```sql
   -- Connect to database
   sqlite3 hr_recruitment.db
   
   -- Update user role
   UPDATE users SET role = 'admin', status = 'active', is_active = 1 
   WHERE email = 'your@email.com';
   
   -- Verify
   SELECT id, full_name, email, role, status FROM users WHERE email = 'your@email.com';
   ```

3. **Contact development team:**
   - Provide error logs
   - Provide user email
   - Provide environment details

---

## 📚 **RELATED DOCUMENTATION**

- `PROJECT_STATUS_AND_ROADMAP.md` - Overall project status
- `CONTEXT_BUNDLE_FOR_NEXT_SESSION.md` - Development context
- `models/database.py` - User model definition
- `services/user_management_service.py` - User management logic
- `api/users.py` - User management API

---

## 🎯 **QUICK REFERENCE**

### **Most Common Use Case:**
```bash
# Promote your existing account to admin
python make_user_admin.py your@email.com
```

### **Production Quick Command:**
```bash
# In Dokploy console
python make_user_admin.py your@email.com
```

### **Verify Admin Access:**
1. Login to application
2. Check for "Users" menu
3. Try accessing `/users` page
4. Success = You're an admin! 🎉

---

**Created by:** Development Team  
**Last Updated:** October 13, 2025  
**Status:** ✅ Ready to use
