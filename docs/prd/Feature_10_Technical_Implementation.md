# Feature 10: User Management - Technical Implementation

**Version**: 1.0  
**Date**: 2025-10-08  
**Author**: Technical Architecture Team  

---

## 1. DATABASE DESIGN

### 1.1 New Tables

#### `user_roles`
```sql
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    permissions JSONB NOT NULL DEFAULT '[]',
    is_system_role BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO user_roles (name, display_name, permissions) VALUES
('hr_admin', 'HR Admin', '["user.manage", "job.create", "job.edit", "job.delete", "resume.upload", "resume.rate", "resume.approve", "candidate.hire", "analytics.view_all", "settings.manage", "audit.view", "data.export"]'::jsonb),
('hr_manager', 'HR Manager', '["job.create", "job.edit", "resume.upload", "resume.rate", "resume.approve", "candidate.hire", "analytics.view_all", "audit.view_readonly", "data.export"]'::jsonb),
('recruiter', 'Recruiter', '["resume.upload", "resume.rate", "analytics.view_own"]'::jsonb);
```

#### `user_activity_log`
```sql
CREATE TABLE user_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(100) NOT NULL,
    action_details JSONB,
    ip_address INET,
    user_agent TEXT,
    location VARCHAR(255),
    session_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'success',
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_activity_log_user_id ON user_activity_log(user_id);
CREATE INDEX idx_user_activity_log_timestamp ON user_activity_log(timestamp DESC);
```

#### `user_sessions`
```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ip_address INET,
    device_type VARCHAR(50),
    browser VARCHAR(100),
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_is_active ON user_sessions(is_active);
```

#### `user_audit_log`
```sql
CREATE TABLE user_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    performed_by UUID NOT NULL REFERENCES users(id),
    ip_address INET,
    timestamp TIMESTAMP DEFAULT NOW(),
    checksum VARCHAR(64)
);

CREATE INDEX idx_user_audit_log_target_user_id ON user_audit_log(target_user_id);
```

#### `bulk_user_operations`
```sql
CREATE TABLE bulk_user_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_type VARCHAR(50) NOT NULL,
    user_ids UUID[] NOT NULL,
    parameters JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    total_count INTEGER NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    error_details JSONB,
    initiated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 1.2 Modifications to Existing Tables

```sql
-- users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active';
ALTER TABLE users ADD COLUMN IF NOT EXISTS deactivated_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS deactivation_reason TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_department ON users(department);
```

---

## 2. API DESIGN

### 2.1 Pydantic Models

**File**: `models/user_management_schemas.py`

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"

class UserRole(str, Enum):
    HR_ADMIN = "hr_admin"
    HR_MANAGER = "hr_manager"
    RECRUITER = "recruiter"

class UserCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    mobile: Optional[str] = None
    role: UserRole
    department: Optional[str] = None
    password_option: str = "auto_generate"
    send_welcome_email: bool = True

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    mobile: Optional[str] = None
    department: Optional[str] = None

class UserRoleChangeRequest(BaseModel):
    new_role: UserRole
    reason: str = Field(..., min_length=10)

class UserDeactivateRequest(BaseModel):
    reason: str
    reason_details: str

class BulkUserOperationRequest(BaseModel):
    user_ids: List[str] = Field(..., max_items=100)
    operation: str
    parameters: Dict[str, Any]
    dry_run: bool = False

class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    department: Optional[str]
    status: str
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    users: List[UserResponse]
    pagination: Dict[str, Any]
    summary: Dict[str, Any]
```

### 2.2 API Endpoints

**File**: `api/users.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from services.user_management_service import UserManagementService
from services.auth_service import get_current_user, require_permission
from core.database import get_db

router = APIRouter(prefix="/api/users", tags=["User Management"])

@router.get("", response_model=UserListResponse)
async def list_users(
    status: Optional[str] = None,
    role: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("user.manage"))
):
    service = UserManagementService(db)
    return await service.list_users(status, role, search, page, limit)

@router.post("", status_code=201)
async def create_user(
    user_data: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("user.manage"))
):
    service = UserManagementService(db)
    return await service.create_user(user_data, current_user)

@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not (current_user.has_permission("user.manage") or current_user.id == user_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    service = UserManagementService(db)
    return await service.get_user_details(user_id)

@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = UserManagementService(db)
    return await service.update_user(user_id, user_data, current_user)

@router.put("/{user_id}/role")
async def change_role(
    user_id: str,
    role_data: UserRoleChangeRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("user.manage"))
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot change own role")
    service = UserManagementService(db)
    return await service.change_user_role(user_id, role_data, current_user)

@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    data: UserDeactivateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("user.manage"))
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    service = UserManagementService(db)
    return await service.deactivate_user(user_id, data, current_user)

@router.get("/{user_id}/activity")
async def get_activity(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    from services.user_activity_service import UserActivityService
    service = UserActivityService(db)
    return await service.get_user_activity(user_id, page, limit)

@router.get("/{user_id}/sessions")
async def get_sessions(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    from services.session_management_service import SessionManagementService
    service = SessionManagementService(db)
    return await service.get_user_sessions(user_id)

@router.delete("/{user_id}/sessions/{session_id}")
async def force_logout(
    user_id: str,
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    from services.session_management_service import SessionManagementService
    service = SessionManagementService(db)
    return await service.terminate_session(session_id)

@router.post("/bulk-operations", status_code=202)
async def bulk_operation(
    data: BulkUserOperationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("user.manage"))
):
    from services.bulk_user_operations_service import BulkUserOperationsService
    service = BulkUserOperationsService(db)
    return await service.initiate_bulk_operation(data, current_user)
```

---

## 3. SERVICE LAYER

### 3.1 User Management Service

**File**: `services/user_management_service.py`

```python
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime
import secrets
import string
from models.database import User
from services.permission_service import PermissionService
from services.user_audit_service import UserAuditService
from services.notification_service import NotificationService

class UserManagementService:
    def __init__(self, db: Session):
        self.db = db
        self.permission_service = PermissionService(db)
        self.audit_service = UserAuditService(db)
        self.notification_service = NotificationService()
    
    async def list_users(self, status, role, search, page, limit):
        """List users with filtering and pagination."""
        query = self.db.query(User)
        
        if status:
            query = query.filter(User.status == status)
        if role:
            query = query.filter(User.role == role)
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(User.full_name).like(search_term),
                    func.lower(User.email).like(search_term)
                )
            )
        
        total = query.count()
        offset = (page - 1) * limit
        users = query.offset(offset).limit(limit).all()
        
        summary = {
            "total_users": total,
            "active": self.db.query(User).filter(User.status == "active").count(),
            "inactive": self.db.query(User).filter(User.status == "inactive").count()
        }
        
        return {
            "users": users,
            "pagination": {"total": total, "page": page, "limit": limit},
            "summary": summary
        }
    
    async def create_user(self, user_data, created_by):
        """Create new user account."""
        # Check email uniqueness
        existing = self.db.query(User).filter(
            func.lower(User.email) == user_data.email.lower()
        ).first()
        if existing:
            raise ValueError("Email already in use")
        
        # Generate password
        temp_password = self._generate_password()
        
        # Create user
        user = User(
            full_name=user_data.full_name,
            email=user_data.email,
            mobile=user_data.mobile,
            role=user_data.role.value,
            department=user_data.department,
            password_hash=self._hash_password(temp_password),
            status="active",
            created_at=datetime.utcnow()
        )
        
        self.db.add(user)
        self.db.commit()
        
        # Audit log
        await self.audit_service.log_user_action(
            target_user_id=user.id,
            action_type="create",
            new_values={"email": user.email, "role": user.role},
            performed_by=created_by.id
        )
        
        # Send welcome email
        if user_data.send_welcome_email:
            await self.notification_service.send_welcome_email(
                user.email, user.full_name, temp_password
            )
        
        return {"id": str(user.id), "temporary_password": temp_password}
    
    async def change_user_role(self, user_id, role_data, changed_by):
        """Change user role."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Check if last admin
        if user.role == "hr_admin":
            admin_count = self.db.query(User).filter(
                User.role == "hr_admin", User.status == "active"
            ).count()
            if admin_count <= 1:
                raise ValueError("Cannot remove last HR Admin")
        
        old_role = user.role
        user.role = role_data.new_role.value
        self.db.commit()
        
        # Audit log
        await self.audit_service.log_user_action(
            target_user_id=user_id,
            action_type="role_change",
            old_values={"role": old_role},
            new_values={"role": user.role, "reason": role_data.reason},
            performed_by=changed_by.id
        )
        
        return {"message": "Role changed successfully"}
    
    async def deactivate_user(self, user_id, data, deactivated_by):
        """Deactivate user account."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        user.status = "inactive"
        user.deactivated_at = datetime.utcnow()
        user.deactivation_reason = f"{data.reason}: {data.reason_details}"
        self.db.commit()
        
        # Terminate all sessions
        from services.session_management_service import SessionManagementService
        session_service = SessionManagementService(self.db)
        await session_service.terminate_all_user_sessions(user_id)
        
        # Audit log
        await self.audit_service.log_user_action(
            target_user_id=user_id,
            action_type="deactivate",
            new_values={"status": "inactive", "reason": user.deactivation_reason},
            performed_by=deactivated_by.id
        )
        
        return {"message": "User deactivated successfully"}
    
    def _generate_password(self, length=12):
        """Generate secure random password."""
        chars = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def _hash_password(self, password):
        """Hash password using bcrypt."""
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
```

### 3.2 User Activity Service

**File**: `services/user_activity_service.py`

```python
from sqlalchemy.orm import Session
from datetime import datetime
import geoip2.database
from user_agents import parse

class UserActivityService:
    def __init__(self, db: Session):
        self.db = db
        self.geoip_reader = geoip2.database.Reader('GeoLite2-City.mmdb')
    
    async def log_activity(self, user_id, action_type, action_details, 
                          ip_address, user_agent, session_id):
        """Log user activity."""
        # Parse location from IP
        location = self._get_location(ip_address)
        
        # Parse device info
        ua = parse(user_agent)
        device_type = "mobile" if ua.is_mobile else "tablet" if ua.is_tablet else "desktop"
        browser = f"{ua.browser.family} {ua.browser.version_string}"
        
        activity = {
            "user_id": user_id,
            "action_type": action_type,
            "action_details": action_details,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "location": location,
            "session_id": session_id,
            "status": "success",
            "timestamp": datetime.utcnow()
        }
        
        self.db.execute(
            "INSERT INTO user_activity_log (user_id, action_type, action_details, "
            "ip_address, user_agent, location, session_id, status, timestamp) "
            "VALUES (:user_id, :action_type, :action_details, :ip_address, "
            ":user_agent, :location, :session_id, :status, :timestamp)",
            activity
        )
        self.db.commit()
    
    async def get_user_activity(self, user_id, page, limit):
        """Get user activity log."""
        offset = (page - 1) * limit
        
        activities = self.db.execute(
            "SELECT * FROM user_activity_log WHERE user_id = :user_id "
            "ORDER BY timestamp DESC LIMIT :limit OFFSET :offset",
            {"user_id": user_id, "limit": limit, "offset": offset}
        ).fetchall()
        
        total = self.db.execute(
            "SELECT COUNT(*) FROM user_activity_log WHERE user_id = :user_id",
            {"user_id": user_id}
        ).scalar()
        
        return {
            "activities": activities,
            "pagination": {"total": total, "page": page, "limit": limit}
        }
    
    def _get_location(self, ip_address):
        """Get location from IP address."""
        try:
            response = self.geoip_reader.city(ip_address)
            return f"{response.city.name}, {response.country.name}"
        except:
            return "Unknown"
```

### 3.3 Session Management Service

**File**: `services/session_management_service.py`

```python
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

class SessionManagementService:
    def __init__(self, db: Session):
        self.db = db
        self.max_sessions = 3
        self.session_timeout_hours = 24
    
    async def create_session(self, user_id, ip_address, user_agent):
        """Create new session."""
        # Check concurrent session limit
        active_sessions = self.db.execute(
            "SELECT COUNT(*) FROM user_sessions WHERE user_id = :user_id AND is_active = true",
            {"user_id": user_id}
        ).scalar()
        
        if active_sessions >= self.max_sessions:
            # Terminate oldest session
            oldest = self.db.execute(
                "SELECT session_id FROM user_sessions WHERE user_id = :user_id "
                "AND is_active = true ORDER BY last_activity_at ASC LIMIT 1",
                {"user_id": user_id}
            ).scalar()
            await self.terminate_session(oldest)
        
        # Create new session
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=self.session_timeout_hours)
        
        self.db.execute(
            "INSERT INTO user_sessions (session_id, user_id, ip_address, user_agent, "
            "created_at, last_activity_at, expires_at, is_active) "
            "VALUES (:session_id, :user_id, :ip_address, :user_agent, :created_at, "
            ":last_activity_at, :expires_at, :is_active)",
            {
                "session_id": session_id,
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.utcnow(),
                "last_activity_at": datetime.utcnow(),
                "expires_at": expires_at,
                "is_active": True
            }
        )
        self.db.commit()
        
        return session_id
    
    async def terminate_session(self, session_id):
        """Terminate a session."""
        self.db.execute(
            "UPDATE user_sessions SET is_active = false WHERE session_id = :session_id",
            {"session_id": session_id}
        )
        self.db.commit()
        return {"message": "Session terminated"}
    
    async def terminate_all_user_sessions(self, user_id):
        """Terminate all sessions for a user."""
        self.db.execute(
            "UPDATE user_sessions SET is_active = false WHERE user_id = :user_id",
            {"user_id": user_id}
        )
        self.db.commit()
    
    async def get_user_sessions(self, user_id):
        """Get all active sessions for a user."""
        sessions = self.db.execute(
            "SELECT * FROM user_sessions WHERE user_id = :user_id AND is_active = true "
            "ORDER BY last_activity_at DESC",
            {"user_id": user_id}
        ).fetchall()
        
        return {"sessions": sessions, "total_sessions": len(sessions)}
```

### 3.4 Bulk Operations Service

**File**: `services/bulk_user_operations_service.py`

```python
from sqlalchemy.orm import Session
from celery import shared_task

class BulkUserOperationsService:
    def __init__(self, db: Session):
        self.db = db
    
    async def initiate_bulk_operation(self, data, initiated_by):
        """Initiate bulk operation."""
        # Validate user_ids
        if len(data.user_ids) > 100:
            raise ValueError("Maximum 100 users allowed")
        
        # Create operation record
        operation = {
            "operation_type": data.operation,
            "user_ids": data.user_ids,
            "parameters": data.parameters,
            "status": "pending",
            "total_count": len(data.user_ids),
            "initiated_by": initiated_by.id
        }
        
        result = self.db.execute(
            "INSERT INTO bulk_user_operations (operation_type, user_ids, parameters, "
            "status, total_count, initiated_by, created_at) "
            "VALUES (:operation_type, :user_ids, :parameters, :status, :total_count, "
            ":initiated_by, :created_at) RETURNING id",
            {**operation, "created_at": datetime.utcnow()}
        )
        operation_id = result.scalar()
        self.db.commit()
        
        # Queue background job
        if not data.dry_run:
            process_bulk_operation.delay(operation_id)
        
        return {"operation_id": str(operation_id), "status": "processing"}

@shared_task
def process_bulk_operation(operation_id):
    """Process bulk operation in background."""
    # Implementation for Celery task
    pass
```

### 3.5 Permission Service

**File**: `services/permission_service.py`

```python
from sqlalchemy.orm import Session

class PermissionService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_permissions(self, user_id):
        """Get all permissions for a user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Get role permissions
        role = self.db.execute(
            "SELECT permissions FROM user_roles WHERE name = :role",
            {"role": user.role}
        ).scalar()
        
        permissions = role if role else []
        
        # Get custom permissions
        custom = self.db.execute(
            "SELECT permission, granted FROM user_permissions WHERE user_id = :user_id",
            {"user_id": user_id}
        ).fetchall()
        
        for perm, granted in custom:
            if granted and perm not in permissions:
                permissions.append(perm)
            elif not granted and perm in permissions:
                permissions.remove(perm)
        
        return permissions
    
    def has_permission(self, user_id, permission):
        """Check if user has specific permission."""
        permissions = self.get_user_permissions(user_id)
        return permission in permissions
```

---

## 4. UI/UX DESIGN

### 4.1 Templates

#### Users Dashboard
**File**: `templates/users/dashboard.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="container-fluid">
    <div class="row mb-4">
        <div class="col">
            <h2>User Management</h2>
        </div>
        <div class="col-auto">
            <button class="btn btn-primary" onclick="showCreateUserModal()">
                <i class="fas fa-plus"></i> Create User
            </button>
        </div>
    </div>
    
    <!-- Summary Cards -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5>Total Users</h5>
                    <h2 id="total-users">0</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5>Active</h5>
                    <h2 id="active-users" class="text-success">0</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5>Inactive</h5>
                    <h2 id="inactive-users" class="text-warning">0</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5>Locked</h5>
                    <h2 id="locked-users" class="text-danger">0</h2>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Filters -->
    <div class="row mb-3">
        <div class="col-md-3">
            <select class="form-control" id="status-filter">
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="locked">Locked</option>
            </select>
        </div>
        <div class="col-md-3">
            <select class="form-control" id="role-filter">
                <option value="">All Roles</option>
                <option value="hr_admin">HR Admin</option>
                <option value="hr_manager">HR Manager</option>
                <option value="recruiter">Recruiter</option>
            </select>
        </div>
        <div class="col-md-6">
            <input type="text" class="form-control" id="search-input" 
                   placeholder="Search by name or email...">
        </div>
    </div>
    
    <!-- Users Table -->
    <div class="card">
        <div class="card-body">
            <table class="table table-hover" id="users-table">
                <thead>
                    <tr>
                        <th><input type="checkbox" id="select-all"></th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Department</th>
                        <th>Status</th>
                        <th>Last Login</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="users-tbody">
                    <!-- Populated by JavaScript -->
                </tbody>
            </table>
            
            <nav>
                <ul class="pagination" id="pagination">
                    <!-- Populated by JavaScript -->
                </ul>
            </nav>
        </div>
    </div>
</div>

<!-- Create User Modal -->
<div class="modal fade" id="createUserModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5>Create New User</h5>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <form id="create-user-form">
                    <div class="form-group">
                        <label>Full Name *</label>
                        <input type="text" class="form-control" name="full_name" required>
                    </div>
                    <div class="form-group">
                        <label>Email *</label>
                        <input type="email" class="form-control" name="email" required>
                    </div>
                    <div class="form-group">
                        <label>Mobile</label>
                        <input type="tel" class="form-control" name="mobile">
                    </div>
                    <div class="form-group">
                        <label>Role *</label>
                        <select class="form-control" name="role" required>
                            <option value="recruiter">Recruiter</option>
                            <option value="hr_manager">HR Manager</option>
                            <option value="hr_admin">HR Admin</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Department</label>
                        <input type="text" class="form-control" name="department">
                    </div>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input" name="send_welcome_email" checked>
                        <label class="form-check-label">Send welcome email</label>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="createUser()">Create User</button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', path='/js/user_management.js') }}"></script>
{% endblock %}
```

### 4.2 JavaScript

**File**: `static/js/user_management.js`

```javascript
let currentPage = 1;
let currentFilters = {};

async function loadUsers() {
    const params = new URLSearchParams({
        page: currentPage,
        limit: 20,
        ...currentFilters
    });
    
    const response = await fetch(`/api/users?${params}`);
    const data = await response.json();
    
    // Update summary cards
    document.getElementById('total-users').textContent = data.summary.total_users;
    document.getElementById('active-users').textContent = data.summary.active;
    document.getElementById('inactive-users').textContent = data.summary.inactive;
    document.getElementById('locked-users').textContent = data.summary.locked;
    
    // Populate table
    const tbody = document.getElementById('users-tbody');
    tbody.innerHTML = '';
    
    data.users.forEach(user => {
        const row = `
            <tr>
                <td><input type="checkbox" class="user-checkbox" value="${user.id}"></td>
                <td>${user.full_name}</td>
                <td>${user.email}</td>
                <td><span class="badge badge-info">${user.role}</span></td>
                <td>${user.department || '-'}</td>
                <td><span class="badge badge-${getStatusColor(user.status)}">${user.status}</span></td>
                <td>${formatDate(user.last_login)}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="viewUser('${user.id}')">View</button>
                    <button class="btn btn-sm btn-warning" onclick="editUser('${user.id}')">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deactivateUser('${user.id}')">Deactivate</button>
                </td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
    
    // Update pagination
    renderPagination(data.pagination);
}

async function createUser() {
    const form = document.getElementById('create-user-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    const response = await fetch('/api/users', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    
    if (response.ok) {
        const result = await response.json();
        alert(`User created! Temporary password: ${result.temporary_password}`);
        $('#createUserModal').modal('hide');
        loadUsers();
    } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
    }
}

async function deactivateUser(userId) {
    const reason = prompt('Reason for deactivation:');
    if (!reason) return;
    
    const response = await fetch(`/api/users/${userId}/deactivate`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            reason: 'other',
            reason_details: reason
        })
    });
    
    if (response.ok) {
        alert('User deactivated successfully');
        loadUsers();
    }
}

function getStatusColor(status) {
    const colors = {
        'active': 'success',
        'inactive': 'warning',
        'locked': 'danger'
    };
    return colors[status] || 'secondary';
}

function formatDate(dateString) {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
}

// Event listeners
document.getElementById('status-filter').addEventListener('change', (e) => {
    currentFilters.status = e.target.value;
    currentPage = 1;
    loadUsers();
});

document.getElementById('role-filter').addEventListener('change', (e) => {
    currentFilters.role = e.target.value;
    currentPage = 1;
    loadUsers();
});

document.getElementById('search-input').addEventListener('input', debounce((e) => {
    currentFilters.search = e.target.value;
    currentPage = 1;
    loadUsers();
}, 500));

// Load on page load
document.addEventListener('DOMContentLoaded', loadUsers);
```

---

## 5. INTEGRATION POINTS

### 5.1 Authentication Integration

**Modify**: `services/auth_service.py`

```python
# Add permission checking
def require_permission(permission: str):
    def decorator(current_user = Depends(get_current_user)):
        from services.permission_service import PermissionService
        perm_service = PermissionService(db)
        if not perm_service.has_permission(current_user.id, permission):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return decorator

# Add to User model
class User:
    def has_permission(self, permission):
        from services.permission_service import PermissionService
        perm_service = PermissionService(db)
        return perm_service.has_permission(self.id, permission)
```

### 5.2 Activity Logging Integration

**Modify**: `api/auth.py`

```python
from services.user_activity_service import UserActivityService

@router.post("/login")
async def login(credentials: LoginRequest, request: Request, db: Session = Depends(get_db)):
    # ... existing login logic ...
    
    # Log activity
    activity_service = UserActivityService(db)
    await activity_service.log_activity(
        user_id=user.id,
        action_type="login",
        action_details={"method": "email_password"},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        session_id=session_id
    )
    
    return {"access_token": token}
```

### 5.3 Job Management Integration

**Modify**: `api/jobs.py`

```python
# Add permission checks
@router.post("/api/jobs")
async def create_job(
    job_data: JobCreateRequest,
    current_user = Depends(require_permission("job.create"))
):
    # ... existing logic ...
    pass

@router.delete("/api/jobs/{job_id}")
async def delete_job(
    job_id: str,
    current_user = Depends(require_permission("job.delete"))
):
    # ... existing logic ...
    pass
```

---

## 6. FILE STRUCTURE

### 6.1 New Files to Create

```
├── api/
│   └── users.py                          # User management API endpoints
├── services/
│   ├── user_management_service.py        # Core user CRUD operations
│   ├── user_activity_service.py          # Activity logging
│   ├── session_management_service.py     # Session management
│   ├── permission_service.py             # Permission checks
│   ├── user_audit_service.py             # Audit logging
│   └── bulk_user_operations_service.py   # Bulk operations
├── models/
│   └── user_management_schemas.py        # Pydantic models
├── templates/
│   └── users/
│       ├── dashboard.html                # Users list page
│       ├── detail.html                   # User detail page
│       └── activity.html                 # Activity log page
├── static/
│   ├── js/
│   │   └── user_management.js            # Frontend logic
│   └── css/
│       └── user_management.css           # Custom styles
├── migrations/
│   └── 010_create_user_management_tables.sql
└── tests/
    ├── test_user_management_service.py
    ├── test_user_activity_service.py
    ├── test_session_management_service.py
    └── test_permission_service.py
```

### 6.2 Files to Modify

```
├── models/database.py                    # Add new columns to User model
├── services/auth_service.py              # Add permission decorators
├── api/auth.py                           # Add activity logging
├── api/jobs.py                           # Add permission checks
├── api/candidates.py                     # Add permission checks
├── main.py                               # Register new router
└── core/config.py                        # Add new config variables
```

---

## 7. TESTING STRATEGY

### 7.1 Unit Tests

**File**: `tests/test_user_management_service.py`

```python
import pytest
from services.user_management_service import UserManagementService

def test_create_user_success(db_session):
    service = UserManagementService(db_session)
    user_data = UserCreateRequest(
        full_name="Test User",
        email="test@example.com",
        role=UserRole.RECRUITER
    )
    result = await service.create_user(user_data, admin_user)
    assert result["id"] is not None
    assert "temporary_password" in result

def test_create_user_duplicate_email(db_session):
    service = UserManagementService(db_session)
    # Create first user
    await service.create_user(user_data1, admin_user)
    # Try to create with same email
    with pytest.raises(ValueError, match="Email already in use"):
        await service.create_user(user_data1, admin_user)

def test_change_role_cannot_remove_last_admin(db_session):
    service = UserManagementService(db_session)
    with pytest.raises(ValueError, match="Cannot remove last HR Admin"):
        await service.change_user_role(
            last_admin_id, 
            UserRoleChangeRequest(new_role=UserRole.RECRUITER, reason="Test"),
            admin_user
        )

def test_deactivate_user_terminates_sessions(db_session):
    service = UserManagementService(db_session)
    # Create user with active session
    # Deactivate user
    await service.deactivate_user(user_id, deactivate_data, admin_user)
    # Check sessions are terminated
    sessions = db_session.execute(
        "SELECT COUNT(*) FROM user_sessions WHERE user_id = :user_id AND is_active = true",
        {"user_id": user_id}
    ).scalar()
    assert sessions == 0
```

### 7.2 Integration Tests

**File**: `tests/integration/test_user_management_api.py`

```python
from fastapi.testclient import TestClient

def test_list_users_api(client: TestClient, admin_token):
    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "pagination" in data

def test_create_user_api_unauthorized(client: TestClient, recruiter_token):
    response = client.post(
        "/api/users",
        json={"full_name": "Test", "email": "test@example.com", "role": "recruiter"},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert response.status_code == 403

def test_deactivate_user_api(client: TestClient, admin_token):
    # Create user
    create_response = client.post("/api/users", json=user_data, headers=headers)
    user_id = create_response.json()["id"]
    
    # Deactivate
    response = client.post(
        f"/api/users/{user_id}/deactivate",
        json={"reason": "resigned", "reason_details": "Test"},
        headers=headers
    )
    assert response.status_code == 200
    
    # Verify status
    user_response = client.get(f"/api/users/{user_id}", headers=headers)
    assert user_response.json()["status"] == "inactive"
```

### 7.3 Manual Testing Checklist

```
User Creation:
☐ Create user with auto-generated password
☐ Create user with activation link
☐ Verify email uniqueness validation
☐ Verify welcome email sent
☐ Verify user appears in list

Role Management:
☐ Change user role from recruiter to manager
☐ Verify cannot change own role
☐ Verify cannot remove last admin
☐ Verify role change logged in audit

User Deactivation:
☐ Deactivate user
☐ Verify all sessions terminated
☐ Verify cannot login after deactivation
☐ Reactivate user
☐ Verify can login after reactivation

Activity Logging:
☐ Verify login logged
☐ Verify job creation logged
☐ Verify resume upload logged
☐ Verify IP and location captured

Session Management:
☐ Login from multiple devices
☐ Verify session limit enforced
☐ Force logout specific session
☐ Verify session terminated

Bulk Operations:
☐ Bulk change role for 10 users
☐ Verify all users updated
☐ Verify audit log for each user
☐ Test with 100 users (limit)
☐ Verify error handling for failures
```

---

## 8. DEPLOYMENT CONSIDERATIONS

### 8.1 Environment Variables

**Add to `.env`**:

```bash
# Session Management
SESSION_TIMEOUT_HOURS=24
MAX_CONCURRENT_SESSIONS=3

# GeoIP
GEOIP_DATABASE_PATH=/path/to/GeoLite2-City.mmdb

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
WELCOME_EMAIL_TEMPLATE=templates/emails/welcome.html

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 8.2 Migration Script

**File**: `migrations/010_create_user_management_tables.sql`

```sql
-- Run this migration to create all user management tables
BEGIN;

-- Create user_roles table
CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    permissions JSONB NOT NULL DEFAULT '[]',
    is_system_role BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert default roles
INSERT INTO user_roles (name, display_name, permissions) VALUES
('hr_admin', 'HR Admin', '["user.manage", "job.create", "job.edit", "job.delete", "resume.upload", "resume.rate", "resume.approve", "candidate.hire", "analytics.view_all", "settings.manage", "audit.view", "data.export"]'::jsonb),
('hr_manager', 'HR Manager', '["job.create", "job.edit", "resume.upload", "resume.rate", "resume.approve", "candidate.hire", "analytics.view_all", "audit.view_readonly", "data.export"]'::jsonb),
('recruiter', 'Recruiter', '["resume.upload", "resume.rate", "analytics.view_own"]'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- Modify users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active';
ALTER TABLE users ADD COLUMN IF NOT EXISTS deactivated_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS deactivation_reason TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);

-- Create user_activity_log table
CREATE TABLE IF NOT EXISTS user_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(100) NOT NULL,
    action_details JSONB,
    ip_address INET,
    user_agent TEXT,
    location VARCHAR(255),
    session_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'success',
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_activity_log_user_id ON user_activity_log(user_id);
CREATE INDEX idx_user_activity_log_timestamp ON user_activity_log(timestamp DESC);

-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ip_address INET,
    device_type VARCHAR(50),
    browser VARCHAR(100),
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_is_active ON user_sessions(is_active);

-- Create user_audit_log table
CREATE TABLE IF NOT EXISTS user_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    performed_by UUID NOT NULL REFERENCES users(id),
    ip_address INET,
    timestamp TIMESTAMP DEFAULT NOW(),
    checksum VARCHAR(64)
);

CREATE INDEX idx_user_audit_log_target_user_id ON user_audit_log(target_user_id);

-- Create bulk_user_operations table
CREATE TABLE IF NOT EXISTS bulk_user_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_type VARCHAR(50) NOT NULL,
    user_ids UUID[] NOT NULL,
    parameters JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    total_count INTEGER NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    error_details JSONB,
    initiated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

COMMIT;
```

### 8.3 Deployment Steps

```bash
# 1. Install dependencies
pip install geoip2 user-agents celery redis

# 2. Download GeoIP database
wget https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb

# 3. Run migrations
python apply_migration.py migrations/010_create_user_management_tables.sql

# 4. Start Celery worker
celery -A services.celery_app worker --loglevel=info

# 5. Start Celery beat (for scheduled tasks)
celery -A services.celery_app beat --loglevel=info

# 6. Restart application
systemctl restart hr-app
```

### 8.4 Post-Deployment Verification

```bash
# 1. Verify tables created
psql -d hr_db -c "\dt user_*"

# 2. Verify default roles inserted
psql -d hr_db -c "SELECT * FROM user_roles;"

# 3. Test API endpoints
curl -X GET http://localhost:8000/api/users \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 4. Check Celery workers
celery -A services.celery_app inspect active

# 5. Monitor logs
tail -f /var/log/hr-app/application.log
```

---

## 9. IMPLEMENTATION CHECKLIST

### Phase 1: Database & Core Services (Week 1-2)
- [ ] Create database migration script
- [ ] Run migrations on dev/staging
- [ ] Create Pydantic models
- [ ] Implement UserManagementService
- [ ] Implement PermissionService
- [ ] Write unit tests for services
- [ ] Test on staging environment

### Phase 2: API & Activity Logging (Week 3-4)
- [ ] Implement API endpoints
- [ ] Add permission decorators
- [ ] Implement UserActivityService
- [ ] Implement SessionManagementService
- [ ] Integrate activity logging with auth
- [ ] Write integration tests
- [ ] Test API endpoints with Postman

### Phase 3: UI & Bulk Operations (Week 5-6)
- [ ] Create HTML templates
- [ ] Implement JavaScript frontend
- [ ] Add CSS styling
- [ ] Implement BulkOperationsService
- [ ] Set up Celery workers
- [ ] Test UI flows manually
- [ ] Cross-browser testing

### Phase 4: Testing & Deployment (Week 7)
- [ ] Complete all unit tests (85% coverage)
- [ ] Complete integration tests
- [ ] Performance testing
- [ ] Security audit
- [ ] Documentation
- [ ] Deploy to staging
- [ ] User acceptance testing
- [ ] Deploy to production

---

**End of Technical Implementation Document**
