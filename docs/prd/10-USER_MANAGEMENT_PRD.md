# PRD: Advanced User Management

**Feature ID:** 10  
**Feature Name:** Advanced User Management  
**Priority:** P1 (High)  
**Complexity:** High  
**Estimated Effort:** 3-4 weeks  
**Phase:** 4 (Advanced Features)  
**Dependencies:** Feature 1 (User Authentication - separate branch)

---

## 1. Overview

### 1.1 Description
Comprehensive user management system with role-based access control (RBAC), granular permissions, activity tracking, password management, and administrative controls.

### 1.2 Business Value
- **Security:** Fine-grained access control
- **Compliance:** Complete audit trail
- **Accountability:** Track all user actions
- **Flexibility:** Module-level permissions
- **Scalability:** Support 100+ users

### 1.3 Success Metrics
- Secure RBAC implementation
- Granular permission control working
- Complete activity logging (100% coverage)
- Password policy enforcement
- Audit trail for compliance

---

## 2. User Stories

### US-10.1: Manage Users (Admin)
```
As an admin
I want to create, edit, and delete user accounts
So that I can control who has access to the system

Acceptance Criteria:
- [ ] Create new user accounts
- [ ] Edit user details
- [ ] Deactivate/activate accounts
- [ ] Delete accounts (soft delete)
- [ ] Bulk user operations
- [ ] Import users from CSV
```

### US-10.2: Assign Roles
```
As an admin
I want to assign roles to users
So that they have appropriate access levels

Acceptance Criteria:
- [ ] Predefined roles: Admin, Hiring Manager, Recruiter, Viewer
- [ ] Assign single role per user
- [ ] Change user role
- [ ] View users by role
- [ ] Role change notification
```

### US-10.3: Configure Permissions
```
As an admin
I want to configure module-level permissions
So that I can control access to features

Acceptance Criteria:
- [ ] Resume upload permission
- [ ] Candidate tracking permission
- [ ] Job creation permission
- [ ] User management permission
- [ ] Reports & analytics permission
- [ ] Custom permission sets
```

### US-10.4: Password Management
```
As an admin
I want to enforce password policies
So that accounts remain secure

Acceptance Criteria:
- [ ] Minimum length (8 characters)
- [ ] Complexity requirements
- [ ] Password expiration (90 days)
- [ ] Password history (last 5)
- [ ] Force password reset
- [ ] Self-service password reset
```

### US-10.5: Activity Logging
```
As an admin
I want to view user activity logs
So that I can monitor system usage and security

Acceptance Criteria:
- [ ] Login/logout tracking
- [ ] Action audit trail
- [ ] Search history
- [ ] Failed login attempts
- [ ] Export activity logs
- [ ] Real-time activity feed
```

### US-10.6: Assign to Jobs/Clients
```
As an admin
I want to assign recruiters to specific jobs
So that they focus on relevant positions

Acceptance Criteria:
- [ ] Assign recruiter to multiple jobs
- [ ] View assigned jobs
- [ ] Remove assignments
- [ ] Limit visibility to assigned jobs only
- [ ] Transfer assignments
```

---

## 3. Functional Requirements

### 3.1 User Roles & Permissions

**FR-10.1.1: Role Definitions**
```python
ROLES = {
    "admin": {
        "name": "Administrator",
        "description": "Full system access",
        "permissions": ["*"]  # All permissions
    },
    "hiring_manager": {
        "name": "Hiring Manager",
        "description": "Manage jobs and candidates",
        "permissions": [
            "jobs.create",
            "jobs.edit",
            "jobs.view",
            "candidates.view",
            "candidates.rate",
            "interviews.schedule",
            "reports.view"
        ]
    },
    "recruiter": {
        "name": "Recruiter",
        "description": "Resume screening and tracking",
        "permissions": [
            "resumes.upload",
            "candidates.view",
            "candidates.filter",
            "candidates.rate",
            "candidates.track",
            "interviews.schedule",
            "jobs.view"
        ]
    },
    "viewer": {
        "name": "Viewer",
        "description": "Read-only access",
        "permissions": [
            "candidates.view",
            "jobs.view",
            "reports.view"
        ]
    }
}
```

**FR-10.1.2: Permission Hierarchy**
```
Module Level:
- resumes.*
  - resumes.upload
  - resumes.view
  - resumes.delete
  
- candidates.*
  - candidates.view
  - candidates.create
  - candidates.edit
  - candidates.filter
  - candidates.rate
  - candidates.track
  
- jobs.*
  - jobs.create
  - jobs.edit
  - jobs.view
  - jobs.delete
  - jobs.publish
  
- users.*
  - users.create
  - users.edit
  - users.view
  - users.delete
  - users.manage_permissions
  
- reports.*
  - reports.view
  - reports.export
```

### 3.2 Password Management

**FR-10.2.1: Password Policy**
```python
PASSWORD_POLICY = {
    "min_length": 8,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special_char": True,
    "expiry_days": 90,
    "history_count": 5,  # Can't reuse last 5 passwords
    "max_failed_attempts": 5,
    "lockout_duration_minutes": 30
}
```

**FR-10.2.2: Password Validation**
```python
def validate_password(password):
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain a number")
    
    if not any(c in "!@#$%^&*" for c in password):
        errors.append("Password must contain special character")
    
    return errors
```

**FR-10.2.3: Password Reset Flow**
```
1. User requests reset
2. System sends email with reset token (expires in 1 hour)
3. User clicks link, enters new password
4. System validates password
5. Password is hashed and saved
6. Password history is updated
7. User is notified of successful reset
```

### 3.3 Activity Logging

**FR-10.3.1: Logged Actions**
```python
LOGGED_ACTIONS = [
    # Authentication
    "user.login.success",
    "user.login.failed",
    "user.logout",
    "user.password_reset",
    
    # User Management
    "user.created",
    "user.updated",
    "user.deleted",
    "user.role_changed",
    "user.deactivated",
    "user.activated",
    
    # Candidates
    "candidate.viewed",
    "candidate.created",
    "candidate.updated",
    "candidate.rated",
    "candidate.status_changed",
    
    # Jobs
    "job.created",
    "job.updated",
    "job.published",
    "job.closed",
    
    # Resumes
    "resume.uploaded",
    "resume.downloaded",
    "resume.deleted",
    
    # Search
    "search.candidates",
    "search.jobs",
    
    # Reports
    "report.generated",
    "report.exported"
]
```

**FR-10.3.2: Log Entry Structure**
```json
{
    "id": 12345,
    "timestamp": "2025-10-06T10:30:00Z",
    "user_id": 5,
    "user_name": "sarah.recruiter",
    "action": "candidate.status_changed",
    "resource_type": "candidate",
    "resource_id": 123,
    "details": {
        "from_status": "screened",
        "to_status": "interviewed",
        "reason": "Passed technical round"
    },
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "session_id": "sess_abc123"
}
```

### 3.4 User Assignments

**FR-10.4.1: Job Assignments**
```python
# Assign recruiter to job
assign_recruiter_to_job(
    recruiter_id=5,
    job_id=123,
    is_primary=True,
    assigned_by=admin_id
)

# Get recruiter's assigned jobs
jobs = get_assigned_jobs(recruiter_id=5)

# Restrict candidate view to assigned jobs only
if user.role == "recruiter" and settings.RESTRICT_BY_ASSIGNMENT:
    candidates = candidates.filter(
        job_candidates__job_id__in=user.assigned_jobs
    )
```

**FR-10.4.2: Client Assignments (Optional)**
```python
# Multi-tenant support
assign_recruiter_to_client(
    recruiter_id=5,
    client_id=10
)
```

---

## 4. Database Schema

```sql
-- Extend users table (from Feature 1)
ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'viewer';
ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;
ALTER TABLE users ADD COLUMN password_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE;

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    module VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    
    UNIQUE (module, action)
);

CREATE TABLE role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_permissions (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    granted_by INTEGER REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (user_id, permission_id)
);

CREATE TABLE password_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_password_history_user (user_id)
);

CREATE TABLE activity_log (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_name VARCHAR(255),
    
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    
    details JSONB,
    
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_activity_log_user (user_id),
    INDEX idx_activity_log_action (action),
    INDEX idx_activity_log_resource (resource_type, resource_id),
    INDEX idx_activity_log_created (created_at DESC)
);

-- Partitioning for activity_log (optional, for scale)
CREATE TABLE activity_log_2025_10 PARTITION OF activity_log
FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP DEFAULT NOW(),
    
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_sessions_user (user_id),
    INDEX idx_sessions_active (is_active, expires_at)
);
```

---

## 5. API Specifications

### 5.1 User CRUD

**Create User**
```
POST /api/users

{
    "email": "recruiter@company.com",
    "full_name": "Sarah Recruiter",
    "role": "recruiter",
    "department": "Talent Acquisition",
    "send_invite_email": true
}
```

**Update User**
```
PATCH /api/users/{id}

{
    "role": "hiring_manager",
    "is_active": true,
    "department": "Engineering"
}
```

**Get Users**
```
GET /api/users?role=recruiter&is_active=true&page=1

Response:
{
    "users": [
        {
            "id": 5,
            "email": "sarah@company.com",
            "full_name": "Sarah Recruiter",
            "role": "recruiter",
            "is_active": true,
            "last_login": "2025-10-06T09:00:00Z",
            "created_at": "2025-09-01T10:00:00Z"
        }
    ],
    "pagination": {...}
}
```

### 5.2 Permissions

**Check Permission**
```
GET /api/users/{id}/permissions/check?permission=candidates.rate

Response:
{
    "user_id": 5,
    "permission": "candidates.rate",
    "has_permission": true,
    "granted_via": "role"  // or "direct"
}
```

**Grant Permission**
```
POST /api/users/{id}/permissions

{
    "permission_id": 15
}
```

### 5.3 Activity Logs

**Get User Activity**
```
GET /api/users/{id}/activity?start_date=2025-10-01&action=candidate.*

Response:
{
    "user_id": 5,
    "activities": [
        {
            "id": 12345,
            "timestamp": "2025-10-06T10:30:00Z",
            "action": "candidate.status_changed",
            "resource": "Candidate #123",
            "details": {...}
        }
    ]
}
```

**Get System Activity**
```
GET /api/activity-log?action=user.login.failed&limit=100

Response: Recent failed login attempts
```

### 5.4 Password Management

**Reset Password (Admin)**
```
POST /api/users/{id}/reset-password

{
    "send_email": true,
    "force_change_on_login": true
}
```

**Change Password (User)**
```
POST /api/users/me/change-password

{
    "current_password": "oldpass123",
    "new_password": "newpass456"
}
```

---

## 6. UI/UX Specifications

### 6.1 User Management Dashboard

```
┌──────────────────────────────────────────────────────────┐
│ 👥 User Management                    [+ Add User]       │
│ ┌─────────┬─────────┬─────────┬─────────┬─────────────┐ │
│ │ Total   │ Active  │ Inactive│ Admins  │ Recruiters  │ │
│ │   45    │   42    │    3    │    2    │     25      │ │
│ └─────────┴─────────┴─────────┴─────────┴─────────────┘ │
├──────────────────────────────────────────────────────────┤
│ Filter: [All Roles ▼] [Active ▼] Search: [          ] 🔍│
├──────────────────────────────────────────────────────────┤
│                                                           │
│ ┌──────────────────────────────────────────────────────┐│
│ │ ☑ Sarah Recruiter          🟢 Active                  ││
│ │   sarah.recruiter@company.com                         ││
│ │   Role: Recruiter | Dept: Talent Acquisition          ││
│ │   Last Login: 2 hours ago | Created: Sep 1, 2025     ││
│ │   Assigned Jobs: 8                                    ││
│ │   [Edit] [Deactivate] [View Activity] [Reset Password]││
│ └──────────────────────────────────────────────────────┘│
│                                                           │
│ ┌──────────────────────────────────────────────────────┐│
│ │ ☐ Mike Manager             🟢 Active                  ││
│ │   mike.manager@company.com                            ││
│ │   Role: Hiring Manager | Dept: Engineering            ││
│ │   Last Login: 1 day ago | Created: Aug 15, 2025      ││
│ │   Assigned Jobs: 12                                   ││
│ │   [Edit] [Deactivate] [View Activity] [Reset Password]││
│ └──────────────────────────────────────────────────────┘│
│                                                           │
│ [Bulk Actions ▼]  [Export Users]  [1][2][3][4]          │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 6.2 Edit User Form

```
┌──────────────────────────────────────────────────────────┐
│ ✏️ Edit User: Sarah Recruiter                            │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ Basic Information                                        │
│ ┌──────────────────────────────────────────────────────┐│
│ │ Full Name *                                           ││
│ │ [Sarah Recruiter                              ]      ││
│ │                                                        ││
│ │ Email *                                                ││
│ │ [sarah.recruiter@company.com                  ]      ││
│ │                                                        ││
│ │ Department                                             ││
│ │ [Talent Acquisition                           ]      ││
│ │                                                        ││
│ │ Phone (Optional)                                       ││
│ │ [+1 555-123-4567                              ]      ││
│ └──────────────────────────────────────────────────────┘│
│                                                           │
│ Role & Permissions                                       │
│ ┌──────────────────────────────────────────────────────┐│
│ │ Role *                                                 ││
│ │ ● Admin  ○ Hiring Manager  ○ Recruiter  ○ Viewer     ││
│ │                                                        ││
│ │ Account Status                                         ││
│ │ ● Active  ○ Inactive                                  ││
│ │                                                        ││
│ │ Custom Permissions (Optional)                          ││
│ │ ☐ Can export all data                                 ││
│ │ ☐ Can manage system settings                          ││
│ └──────────────────────────────────────────────────────┘│
│                                                           │
│ Job Assignments                                          │
│ ┌──────────────────────────────────────────────────────┐│
│ │ Assigned Jobs (8):                                     ││
│ │ ☑ Senior Software Engineer                            ││
│ │ ☑ Product Manager                                     ││
│ │ ☑ DevOps Engineer                                     ││
│ │ [+ Assign to Jobs]                                    ││
│ └──────────────────────────────────────────────────────┘│
│                                                           │
│ [Cancel] [Save Changes] [Force Password Reset]          │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 6.3 Activity Log View

```
┌──────────────────────────────────────────────────────────┐
│ 📊 Activity Log: Sarah Recruiter                         │
│ Period: Last 30 days                                     │
│ Filter: [All Actions ▼] Export: [CSV ▼]                 │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ Oct 6, 2025 10:30 AM                                     │
│ 👤 Status Changed: Candidate #123                        │
│ Changed from "Screened" to "Interviewed"                 │
│ IP: 192.168.1.100                                        │
│                                                           │
│ Oct 6, 2025 09:15 AM                                     │
│ 🔍 Searched Candidates                                   │
│ Query: "Python AND 5+ years experience"                  │
│ Results: 45 candidates                                   │
│                                                           │
│ Oct 6, 2025 09:00 AM                                     │
│ 🔐 Logged In                                             │
│ IP: 192.168.1.100                                        │
│ Browser: Chrome 118                                      │
│                                                           │
│ Oct 5, 2025 5:45 PM                                      │
│ 📤 Uploaded Resume                                       │
│ File: john_doe_resume.pdf (2.3 MB)                       │
│                                                           │
│ [Load More] [1][2][3][4][5]                              │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 7. Implementation Plan

### Week 1: Database & RBAC
- Database schema
- Role and permission models
- Permission checking middleware
- Unit tests

### Week 2: User Management
- User CRUD APIs
- Password management
- Role assignment
- Integration tests

### Week 3: Activity Logging
- Logging middleware
- Activity log APIs
- Search and filtering
- Performance testing

### Week 4: UI & Polish
- User management UI
- Activity log viewer
- Permission configuration
- E2E tests

---

## 8. Security Considerations

**Authentication:**
- JWT tokens with expiry
- Refresh token rotation
- Session management
- CSRF protection

**Authorization:**
- Role-based access control
- Permission checks on every request
- Resource-level permissions
- Deny by default

**Password Security:**
- bcrypt hashing (cost factor 12)
- Password complexity requirements
- Password history
- Account lockout after failed attempts

**Audit & Compliance:**
- Complete activity logging
- Immutable audit trail
- GDPR compliance (data export/deletion)
- SOC 2 compliance ready

---

**Status:** Ready for Implementation  
**Dependencies:** Feature 1 (User Authentication)  
**Critical:** Security-first implementation required
