# Feature 10: User Management - Quick Start Guide

## 🚀 Getting Started

### Step 1: Run the Migration

```bash
# Apply the database migration
python apply_migration.py migrations/010_create_user_management_tables.sql
```

### Step 2: Verify Installation

```bash
# Check if tables were created
sqlite3 hr_recruitment.db ".tables"

# Verify default roles
sqlite3 hr_recruitment.db "SELECT name, display_name FROM user_roles;"
```

### Step 3: Start the Application

```bash
uvicorn main:app --reload
```

### Step 4: Access the Dashboard

Navigate to: `http://localhost:8000/users`

---

## 📋 Common Tasks

### Create a New User

**Via UI:**
1. Go to `/users`
2. Click "Create User" button
3. Fill in the form:
   - Full Name (required)
   - Email (required, must be unique)
   - Mobile (optional)
   - Role (admin/manager/recruiter)
   - Department (optional)
4. Click "Create User"
5. Copy the temporary password shown

**Via API:**
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Doe",
    "email": "jane@example.com",
    "role": "recruiter",
    "department": "Sales"
  }'
```

### Change User Role

**Via API:**
```bash
curl -X PUT http://localhost:8000/api/users/USER_ID/role \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_role": "manager",
    "reason": "Promoted to team lead"
  }'
```

### Deactivate a User

**Via UI:**
1. Find the user in the list
2. Click the red "Deactivate" button
3. Select reason and provide details
4. Confirm deactivation

**Via API:**
```bash
curl -X POST http://localhost:8000/api/users/USER_ID/deactivate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "resigned",
    "reason_details": "Last day: 2025-10-15"
  }'
```

### Search and Filter Users

**Via UI:**
- Use the status dropdown to filter by active/inactive/locked
- Use the role dropdown to filter by admin/manager/recruiter
- Type in the search box to search by name or email
- Type in department field to filter by department

**Via API:**
```bash
# Filter active recruiters in Engineering
curl -X GET "http://localhost:8000/api/users?status=active&role=recruiter&department=Engineering" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Search by name or email
curl -X GET "http://localhost:8000/api/users?search=john" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔐 Permission System

### Role Permissions

| Feature | Admin | Manager | Recruiter |
|---------|-------|---------|-----------|
| Manage Users | ✓ | ✗ | ✗ |
| Create/Edit Jobs | ✓ | ✓ | ✗ |
| Delete Jobs | ✓ | ✗ | ✗ |
| Upload Resumes | ✓ | ✓ | ✓ |
| Rate Resumes | ✓ | ✓ | ✓ |
| Hire Candidates | ✓ | ✓ | ✗ |
| View All Analytics | ✓ | ✓ | ✗ |
| Export Data | ✓ | ✓ | ✗ |

### Check Permissions

```bash
# Get permission matrix
curl -X GET http://localhost:8000/api/users/permissions/matrix \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔍 Troubleshooting

### Issue: Cannot create users

**Solution:**
- Ensure you're logged in as an admin
- Check that the email is unique
- Verify the migration ran successfully

### Issue: Cannot change role

**Solution:**
- You cannot change your own role
- Cannot remove the last admin
- Ensure you have `user.manage` permission

### Issue: Dashboard not loading

**Solution:**
- Check browser console for errors
- Verify API token is valid
- Ensure `/api/users` endpoint is accessible

### Issue: Migration fails

**Solution:**
```bash
# Check if tables already exist
sqlite3 hr_recruitment.db ".schema user_roles"

# If tables exist, migration already ran
# If not, check for SQL syntax errors in migration file
```

---

## 📊 Monitoring

### View Audit Logs

```bash
# Check user audit logs
sqlite3 hr_recruitment.db "SELECT * FROM user_audit_log ORDER BY timestamp DESC LIMIT 10;"

# Check specific user's audit trail
sqlite3 hr_recruitment.db "SELECT action_type, performed_by, timestamp FROM user_audit_log WHERE target_user_id = 'USER_ID';"
```

### Check Active Users

```bash
sqlite3 hr_recruitment.db "SELECT COUNT(*) FROM users WHERE status = 'active';"
```

### View User Statistics

```bash
# Users by role
sqlite3 hr_recruitment.db "SELECT role, COUNT(*) FROM users GROUP BY role;"

# Users by status
sqlite3 hr_recruitment.db "SELECT status, COUNT(*) FROM users GROUP BY status;"
```

---

## 🎯 Best Practices

1. **Always provide a reason** when changing roles or deactivating users
2. **Use bulk operations** for managing multiple users (when implemented)
3. **Review audit logs regularly** for security monitoring
4. **Maintain at least 2 active admins** for redundancy
5. **Deactivate users immediately** when they leave the organization
6. **Use strong passwords** - the system auto-generates secure ones
7. **Assign appropriate roles** - follow principle of least privilege

---

## 📞 Support

For issues or questions:
1. Check the implementation summary: `FEATURE_10_IMPLEMENTATION_SUMMARY.md`
2. Review the technical spec: `docs/prd/Feature_10_Technical_Implementation.md`
3. Check API documentation: `http://localhost:8000/docs`

---

## ✅ Quick Checklist

After deployment, verify:
- [ ] Migration completed successfully
- [ ] Default roles created (admin, manager, recruiter)
- [ ] Can access `/users` dashboard
- [ ] Can create a new user
- [ ] Can change user role
- [ ] Can deactivate user
- [ ] Filters and search work
- [ ] Pagination works with 20+ users
- [ ] Permission checks prevent unauthorized actions
- [ ] Audit logs are being created
