"""Pydantic schemas for Client Management"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# CLIENT SCHEMAS
# ============================================================================

class ClientBase(BaseModel):
    """Base client schema"""
    company_name: str = Field(..., min_length=2, max_length=200)
    company_email: EmailStr
    company_phone: Optional[str] = Field(None, max_length=20)
    company_website: Optional[str] = Field(None, max_length=255)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Business details
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, pattern="^(1-10|11-50|51-200|201-500|501-1000|1000\\+)$")
    tax_id: Optional[str] = Field(None, max_length=50)
    
    # Contract details
    contract_type: Optional[str] = Field(None, pattern="^(monthly|annual|project-based)$")
    billing_cycle: Optional[str] = Field(None, pattern="^(monthly|quarterly|annual)$")
    
    # Notes
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    """Schema for creating a client"""
    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client"""
    company_name: Optional[str] = Field(None, min_length=2, max_length=200)
    company_email: Optional[EmailStr] = None
    company_phone: Optional[str] = Field(None, max_length=20)
    company_website: Optional[str] = Field(None, max_length=255)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Business details
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = None
    tax_id: Optional[str] = Field(None, max_length=50)
    
    # Status
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended|pending)$")
    
    # Contract details
    contract_type: Optional[str] = None
    billing_cycle: Optional[str] = None
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    
    # Notes
    notes: Optional[str] = None


class ClientResponse(ClientBase):
    """Schema for client response"""
    id: str
    status: str
    is_active: bool
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deactivated_at: Optional[datetime] = None
    
    # Counts
    contacts_count: Optional[int] = 0
    jobs_count: Optional[int] = 0
    active_jobs_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ClientListResponse(BaseModel):
    """Schema for client list response"""
    clients: List[ClientResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# CLIENT CONTACT SCHEMAS
# ============================================================================

class ClientContactBase(BaseModel):
    """Base client contact schema"""
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    designation: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    is_primary: bool = False
    has_portal_access: bool = False
    notes: Optional[str] = None


class ClientContactCreate(ClientContactBase):
    """Schema for creating a client contact"""
    client_id: str


class ClientContactUpdate(BaseModel):
    """Schema for updating a client contact"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    designation: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None
    has_portal_access: Optional[bool] = None
    notes: Optional[str] = None


class ClientContactResponse(ClientContactBase):
    """Schema for client contact response"""
    id: str
    client_id: str
    is_active: bool
    portal_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# CLIENT JOB SCHEMAS
# ============================================================================

class ClientJobBase(BaseModel):
    """Base client job schema"""
    job_title: str = Field(..., min_length=2, max_length=200)
    job_description: Optional[str] = None
    requirements: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    job_type: Optional[str] = Field(None, pattern="^(full-time|part-time|contract|internship)$")
    experience_required: Optional[str] = Field(None, max_length=50)
    salary_range: Optional[str] = Field(None, max_length=100)
    positions_count: int = Field(1, ge=1)
    priority: str = Field("medium", pattern="^(low|medium|high|urgent)$")
    deadline: Optional[datetime] = None


class ClientJobCreate(ClientJobBase):
    """Schema for creating a client job"""
    client_id: str
    job_id: Optional[str] = None  # Link to existing job if applicable


class ClientJobUpdate(BaseModel):
    """Schema for updating a client job"""
    job_title: Optional[str] = Field(None, min_length=2, max_length=200)
    job_description: Optional[str] = None
    requirements: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    job_type: Optional[str] = None
    experience_required: Optional[str] = Field(None, max_length=50)
    salary_range: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, pattern="^(open|closed|on_hold|filled|cancelled)$")
    positions_count: Optional[int] = Field(None, ge=1)
    priority: Optional[str] = None
    deadline: Optional[datetime] = None


class ClientJobResponse(ClientJobBase):
    """Schema for client job response"""
    id: str
    client_id: str
    job_id: Optional[str] = None
    status: str
    applications_count: int
    shortlisted_count: int
    hired_count: int
    posted_date: datetime
    filled_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# CLIENT ACTIVITY SCHEMAS
# ============================================================================

class ClientActivityBase(BaseModel):
    """Base client activity schema"""
    activity_type: str = Field(..., pattern="^(meeting|call|email|job_posted|contract_signed|payment_received|other)$")
    activity_title: str = Field(..., min_length=2, max_length=200)
    activity_description: Optional[str] = None
    contact_id: Optional[str] = None
    scheduled_date: Optional[datetime] = None


class ClientActivityCreate(ClientActivityBase):
    """Schema for creating a client activity"""
    client_id: str


class ClientActivityUpdate(BaseModel):
    """Schema for updating a client activity"""
    activity_title: Optional[str] = Field(None, min_length=2, max_length=200)
    activity_description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(scheduled|completed|cancelled|rescheduled)$")
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None


class ClientActivityResponse(ClientActivityBase):
    """Schema for client activity response"""
    id: str
    client_id: str
    status: str
    performed_by: Optional[str] = None
    activity_date: datetime
    completed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# FILTER & SEARCH SCHEMAS
# ============================================================================

class ClientFilter(BaseModel):
    """Schema for filtering clients"""
    search_query: Optional[str] = None
    status: Optional[List[str]] = None
    industry: Optional[str] = None
    company_size: Optional[List[str]] = None
    city: Optional[str] = None
    country: Optional[str] = None
    has_active_jobs: Optional[bool] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


class ClientDeactivateRequest(BaseModel):
    """Schema for deactivating a client"""
    reason: str = Field(..., min_length=10, max_length=500)


class ClientReactivateRequest(BaseModel):
    """Schema for reactivating a client"""
    notes: Optional[str] = Field(None, max_length=500)
