"""Pydantic schemas for user management"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    PENDING_ACTIVATION = "pending_activation"


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    RECRUITER = "recruiter"


class PasswordOption(str, Enum):
    AUTO_GENERATE = "auto_generate"
    USER_SET_ON_FIRST_LOGIN = "user_set_on_first_login"


class DeactivationReason(str, Enum):
    RESIGNED = "resigned"
    TERMINATED = "terminated"
    ON_LEAVE = "on_leave"
    OTHER = "other"


# Request Schemas
class UserCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    mobile: Optional[str] = Field(None, pattern=r'^(\+?[1-9]\d{0,14})?$')
    role: UserRole
    department: Optional[str] = Field(None, max_length=100)
    password_option: PasswordOption = PasswordOption.AUTO_GENERATE
    send_welcome_email: bool = True
    status: UserStatus = UserStatus.ACTIVE


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    mobile: Optional[str] = Field(None, pattern=r'^(\+?[1-9]\d{0,14})?$')
    role: Optional[UserRole] = None
    department: Optional[str] = Field(None, max_length=100)
    status: Optional[UserStatus] = None
    new_password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserRoleChangeRequest(BaseModel):
    new_role: UserRole
    reason: str = Field(..., min_length=10, max_length=500)


class UserDeactivateRequest(BaseModel):
    reason: DeactivationReason
    reason_details: str = Field(..., min_length=10, max_length=1000)
    effective_date: Optional[datetime] = None


class UserReactivateRequest(BaseModel):
    send_notification: bool = True
    reset_password: bool = True


class BulkUserOperationRequest(BaseModel):
    user_ids: List[str] = Field(..., min_length=1, max_length=100)
    operation: str = Field(..., pattern=r'^(role_change|deactivate|activate|password_reset|department_change)$')
    parameters: Dict[str, Any]
    dry_run: bool = False


# Response Schemas
class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    mobile: Optional[str]
    role: str
    department: Optional[str]
    status: str
    last_login: Optional[datetime]
    last_activity_at: Optional[datetime]
    created_at: datetime
    active_sessions: int = 0

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    email_verified: bool
    updated_at: datetime
    failed_login_attempts: int
    password_changed_at: Optional[datetime]
    permissions: List[str] = []
    custom_permissions: List[Dict[str, Any]] = []
    statistics: Dict[str, Any] = {}


class UserCreateResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    status: str
    temporary_password: Optional[str] = None
    activation_link: Optional[str] = None
    message: str


class UserListResponse(BaseModel):
    users: List[UserResponse]
    pagination: Dict[str, Any]
    summary: Dict[str, Any]


class ActivityLogEntry(BaseModel):
    id: str
    action_type: str
    action_details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    location: Optional[str]
    user_agent: Optional[str]
    device_type: Optional[str]
    browser: Optional[str]
    status: str
    timestamp: datetime


class UserActivityResponse(BaseModel):
    user_id: str
    activities: List[ActivityLogEntry]
    pagination: Dict[str, Any]
    summary: Dict[str, Any]


class SessionInfo(BaseModel):
    id: str
    session_id: str
    ip_address: Optional[str]
    location: Optional[str]
    device_type: Optional[str]
    browser: Optional[str]
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    is_active: bool
    is_current: bool = False


class UserSessionsResponse(BaseModel):
    user_id: str
    sessions: List[SessionInfo]
    total_sessions: int
    max_sessions: int = 3


class BulkOperationResponse(BaseModel):
    operation_id: str
    status: str
    total_count: int
    message: str


class BulkOperationStatusResponse(BaseModel):
    operation_id: str
    operation_type: str
    status: str
    total_count: int
    success_count: int
    failure_count: int
    error_details: List[Dict[str, Any]]
    parameters: Dict[str, Any]
    initiated_by: Dict[str, str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class PermissionMatrixResponse(BaseModel):
    roles: List[Dict[str, Any]]
    all_permissions: List[Dict[str, Any]]
