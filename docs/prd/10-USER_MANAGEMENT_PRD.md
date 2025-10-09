# Feature 10: User Management - Product Requirements Document

**Document Version**: 1.0  
**Last Updated**: 2025-10-08  
**Status**: Draft  
**Owner**: Product Team  

---

## 1. OVERVIEW

### Description
User Management is a comprehensive user administration system providing HR Admins with centralized control over user accounts, role-based access control (RBAC), permissions management, and activity monitoring.

### Problem Statement
- **Manual User Setup**: No streamlined process for creating and configuring new user accounts
- **Permission Confusion**: Unclear role boundaries leading to security risks
- **No Activity Tracking**: Lack of visibility into user actions and system usage
- **Session Management Gaps**: No centralized control over active sessions
- **Audit Compliance**: Insufficient logging for regulatory compliance

### Target Users
1. **HR Admins** (Primary) - Full user management capabilities
2. **HR Managers** (Secondary) - View team member information
3. **System Administrators** (Secondary) - Technical user management

---

## 2. USER STORIES

### Story 1: User Account Creation
**As an** HR Admin  
**I want** to create new user accounts with appropriate roles and permissions  
**So that** new team members can access the system with the right level of access from day one

### Story 2: Role-Based Access Control
**As an** HR Admin  
**I want** to assign and modify user roles (Admin/Manager/Recruiter) with predefined permission sets  
**So that** I can ensure users only have access to features appropriate for their responsibilities

### Story 3: User Activity Monitoring
**As an** HR Admin  
**I want** to view comprehensive activity logs for all users including login history and actions performed  
**So that** I can monitor system usage, identify security issues, and ensure compliance

### Story 4: User Deactivation and Reactivation
**As an** HR Admin  
**I want** to deactivate user accounts when employees leave and reactivate them if they return  
**So that** I can maintain security while preserving historical data

### Story 5: Bulk User Operations
**As an** HR Admin  
**I want** to perform bulk operations on multiple users (role changes, deactivation, permission updates)  
**So that** I can efficiently manage organizational changes

### Story 6: Session Management
**As an** HR Admin  
**I want** to view active user sessions and force logout specific users if needed  
**So that** I can respond to security incidents immediately

---

## 3. ACCEPTANCE CRITERIA

### Story 1: User Account Creation

**Functional Requirements**:
- [ ] Create user form with fields: full name, email, mobile, role, department
- [ ] Email uniqueness validation (real-time check)
- [ ] Password generation options: auto-generate or user set on first login
- [ ] Send welcome email with login credentials or activation link
- [ ] Bulk user creation via CSV upload (max 100 users)

**Non-Functional Requirements**:
- User creation completes in < 2 seconds
- Password requirements: min 8 chars, uppercase, lowercase, number, special char

### Story 2: Role-Based Access Control

**Functional Requirements**:
- [ ] Three predefined roles: HR Admin, HR Manager, Recruiter
- [ ] Permission matrix clearly displayed for each role
- [ ] Prevent changing own role
- [ ] Prevent removing last HR Admin
- [ ] Role changes effective immediately
- [ ] Audit log entry for every role change

**Permission Matrix**:

| Permission | HR Admin | HR Manager | Recruiter |
|------------|----------|------------|-----------|
| User Management | ✓ | ✗ | ✗ |
| Create/Edit Jobs | ✓ | ✓ | ✗ |
| Delete Jobs | ✓ | ✗ | ✗ |
| Upload Resumes | ✓ | ✓ | ✓ |
| Rate Resumes | ✓ | ✓ | ✓ |
| Approve Ratings | ✓ | ✓ | ✗ |
| Hire Candidate | ✓ | ✓ | ✗ |
| View Analytics | ✓ | ✓ | ✓ (own only) |
| System Settings | ✓ | ✗ | ✗ |
| Audit Logs | ✓ | ✓ (read-only) | ✗ |

### Story 3: User Activity Monitoring

**Functional Requirements**:
- [ ] Activity dashboard showing login history, actions performed, failed login attempts
- [ ] Filter by: user, date range, action type, IP address
- [ ] Export activity log as CSV
- [ ] Real-time activity feed (last 24 hours)
- [ ] Anomaly detection for suspicious activity

**Non-Functional Requirements**:
- Activity log loads in < 2 seconds
- Activity data retained for 2 years

### Story 4: User Deactivation and Reactivation

**Functional Requirements**:
- [ ] Deactivate user button with confirmation dialog
- [ ] Deactivation reason field (required)
- [ ] Immediate logout from all sessions
- [ ] Reactivation sends email notification
- [ ] Soft delete vs. hard delete options
- [ ] Bulk deactivation (max 50 users)

### Story 5: Bulk User Operations

**Functional Requirements**:
- [ ] Bulk actions: Change role, Deactivate/Activate, Update department, Reset password
- [ ] Preview changes before confirmation
- [ ] Progress indicator for bulk operations
- [ ] Error handling with detailed error report
- [ ] Maximum 100 users per operation

### Story 6: Session Management

**Functional Requirements**:
- [ ] Active sessions dashboard showing user, login time, IP address, device
- [ ] Force logout button per session
- [ ] Session timeout configuration (default: 24 hours)
- [ ] Concurrent session limit per user (default: 3)

---

## 4. TECHNICAL DESIGN

### Database Schema

#### Table: `users` (Modifications)
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active';
ALTER TABLE users ADD COLUMN IF NOT EXISTS deactivated_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS deactivation_reason TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);
```

#### Table: `user_roles`
```sql
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL,
    is_system_role BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Table: `user_activity_log`
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
    status VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_activity_log_user_id (user_id),
    INDEX idx_user_activity_log_timestamp (timestamp),
    INDEX idx_user_activity_log_action_type (action_type)
);
```

#### Table: `user_sessions`
```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(50),
    browser VARCHAR(100),
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    
    INDEX idx_user_sessions_user_id (user_id),
    INDEX idx_user_sessions_expires_at (expires_at)
);
```

#### Table: `user_audit_log`
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
    checksum VARCHAR(64),
    
    INDEX idx_user_audit_log_target_user_id (target_user_id),
    INDEX idx_user_audit_log_timestamp (timestamp)
);
```

### API Endpoints

#### 1. List Users
```
GET /api/users
Query: status, role, department, search, sort_by, page, limit
Response: users[], pagination, summary
```

#### 2. Create User
```
POST /api/users
Body: {full_name, email, mobile, role, department, password_option, send_welcome_email}
Response: {id, temporary_password or activation_link}
```

#### 3. Update User
```
PUT /api/users/{user_id}
Body: {full_name, mobile, department, role}
```

#### 4. Change User Role
```
PUT /api/users/{user_id}/role
Body: {new_role, reason}
```

#### 5. Deactivate User
```
POST /api/users/{user_id}/deactivate
Body: {reason, reason_details, effective_date}
```

#### 6. Get User Activity
```
GET /api/users/{user_id}/activity
Query: action_type, date_from, date_to, page, limit
```

#### 7. Get Active Sessions
```
GET /api/users/{user_id}/sessions
Response: sessions[], total_sessions, max_sessions
```

#### 8. Force Logout
```
DELETE /api/users/{user_id}/sessions/{session_id}
```

#### 9. Bulk Operations
```
POST /api/users/bulk-operations
Body: {user_ids[], operation, parameters, dry_run}
Response: {operation_id, status}
```

---

## 5. DEPENDENCIES

### External Libraries
```
pydantic[email]==2.5.0
phonenumbers==8.13.26
redis==5.0.1
bcrypt==4.1.1
geoip2==4.7.0
user-agents==2.2.0
celery==5.3.4
pandas==2.1.3
fastapi-mail==1.4.1
```

### External Services
- Email Service (SendGrid/AWS SES)
- GeoIP Service (MaxMind GeoIP2)
- Redis (Session storage, Celery broker)

### New Modules to Create
1. `services/user_management_service.py`
2. `services/user_activity_service.py`
3. `services/session_management_service.py`
4. `services/permission_service.py`
5. `api/users.py`

---

## 6. TESTING PLAN

### Unit Tests
- User CRUD operations
- Role and permission management
- Session management
- Activity logging
- Bulk operations
- Audit logging

### Integration Tests
- User management API endpoints
- Role management flow
- Session management flow
- Activity logging flow
- Bulk operations end-to-end

### Manual Testing Scenarios
1. User creation and onboarding
2. Role change and permission enforcement
3. User deactivation
4. Activity monitoring
5. Bulk role change
6. Session management

---

## 7. IMPLEMENTATION PLAN

### Phase 1: Core User Management (Week 1-2) - 65 hours
- Database schema setup
- User management service
- Role & permission service
- API endpoints (CRUD)
- Users dashboard UI

### Phase 2: Activity & Sessions (Week 3-4) - 70 hours
- User activity service
- Session management service
- Activity & session API endpoints
- Activity log UI
- Session management UI

### Phase 3: Advanced Features (Week 5-6) - 65 hours
- User audit service
- Bulk operations service
- Bulk operations API
- Role management UI
- Bulk operations UI

### Phase 4: Testing & Documentation (Week 7) - 35 hours
- Comprehensive testing (85% coverage)
- Performance optimization
- Security review
- Documentation

**Total**: 7 weeks, 235 hours

---

## 8. SUCCESS METRICS

### Primary Metrics
1. **Feature Adoption**: 100% of HR Admins use within first week
2. **User Onboarding Time**: Reduce by 70% (from 30min to <10min)
3. **Permission Support Tickets**: Reduce by 60%
4. **Bulk Operations Usage**: 40% of multi-user changes via bulk

### Performance Metrics
1. **User List Load**: < 1s for 10,000+ users
2. **Session Validation**: < 50ms per validation
3. **Activity Log Query**: < 2s for filtered queries
4. **Bulk Operations**: < 30s for 100 users
5. **System Uptime**: 99.5%

### Quality Metrics
1. **Bug Rate**: < 2 critical bugs/month
2. **Test Coverage**: ≥ 85%
3. **API Error Rate**: < 0.5%
4. **Security Incidents**: 0

### Monitoring
- Daily: API error rates, system uptime, background job failures
- Weekly: Feature usage statistics, performance metrics
- Monthly: All success metrics, user satisfaction surveys

---

**End of Document**
