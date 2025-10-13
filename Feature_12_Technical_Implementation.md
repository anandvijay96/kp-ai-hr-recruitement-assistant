# Feature 12: Vendor Management - Technical Implementation Guide

**Version**: 1.0  
**Date**: 2025-10-10  
**Status**: Implementation Ready

---

## 📋 Implementation Overview

This document provides step-by-step technical guidance for implementing the Vendor Management module based on the PRD (Feature_12_Vendor_Management_PRD.md).

---

## 🗄️ Phase 1: Database Implementation

### Step 1: Create Database Migration Script

**File**: `migrations/012_add_vendor_management_tables.sql`

```sql
-- ============================================================================
-- FEATURE 12: VENDOR MANAGEMENT TABLES
-- ============================================================================

-- Main Vendors Table
CREATE TABLE IF NOT EXISTS vendors (
    id VARCHAR(36) PRIMARY KEY,
    vendor_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    service_category VARCHAR(100) NOT NULL,
    contact_person VARCHAR(255),
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50),
    alternate_contact VARCHAR(255),
    website VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    tax_id VARCHAR(100),
    logo_url VARCHAR(500),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    overall_rating DECIMAL(3,2),
    total_contracts INTEGER DEFAULT 0,
    active_contracts INTEGER DEFAULT 0,
    vendor_manager_id VARCHAR(36),
    created_by VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMP,
    deactivation_reason TEXT,
    last_evaluation_date DATE,
    compliance_status VARCHAR(50) DEFAULT 'pending',
    
    FOREIGN KEY (vendor_manager_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    CHECK (status IN ('active', 'inactive', 'on-hold', 'blacklisted')),
    CHECK (overall_rating >= 0 AND overall_rating <= 5)
);

CREATE INDEX idx_vendors_status ON vendors(status);
CREATE INDEX idx_vendors_service_category ON vendors(service_category);
CREATE INDEX idx_vendors_vendor_manager ON vendors(vendor_manager_id);

-- Vendor Contracts Table
CREATE TABLE IF NOT EXISTS vendor_contracts (
    id VARCHAR(36) PRIMARY KEY,
    vendor_id VARCHAR(36) NOT NULL,
    contract_number VARCHAR(100) UNIQUE NOT NULL,
    contract_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    contract_value DECIMAL(15,2),
    currency VARCHAR(10) DEFAULT 'USD',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    payment_terms TEXT,
    renewal_terms TEXT,
    file_url VARCHAR(500) NOT NULL,
    file_name VARCHAR(255),
    file_size INTEGER,
    version INTEGER DEFAULT 1,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    approval_status VARCHAR(50) DEFAULT 'pending',
    approved_by VARCHAR(36),
    approved_at TIMESTAMP,
    termination_date DATE,
    termination_reason TEXT,
    auto_renew BOOLEAN DEFAULT FALSE,
    renewal_notice_days INTEGER DEFAULT 90,
    created_by VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parent_contract_id VARCHAR(36),
    
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_contract_id) REFERENCES vendor_contracts(id),
    CHECK (status IN ('draft', 'pending_approval', 'approved', 'active', 'expired', 'terminated'))
);

CREATE INDEX idx_vendor_contracts_vendor ON vendor_contracts(vendor_id);
CREATE INDEX idx_vendor_contracts_status ON vendor_contracts(status);

-- Performance Reviews Table
CREATE TABLE IF NOT EXISTS vendor_performance_reviews (
    id VARCHAR(36) PRIMARY KEY,
    vendor_id VARCHAR(36) NOT NULL,
    review_period VARCHAR(50) NOT NULL,
    review_date DATE NOT NULL,
    review_type VARCHAR(50) NOT NULL,
    service_quality_rating INTEGER NOT NULL,
    timeliness_rating INTEGER NOT NULL,
    communication_rating INTEGER NOT NULL,
    cost_effectiveness_rating INTEGER NOT NULL,
    compliance_rating INTEGER NOT NULL,
    overall_rating DECIMAL(3,2) NOT NULL,
    strengths TEXT,
    areas_for_improvement TEXT,
    recommendations TEXT,
    written_feedback TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    finalized_by VARCHAR(36),
    finalized_at TIMESTAMP,
    reviewed_by VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
    FOREIGN KEY (finalized_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
    CHECK (service_quality_rating BETWEEN 1 AND 5),
    CHECK (timeliness_rating BETWEEN 1 AND 5),
    CHECK (communication_rating BETWEEN 1 AND 5),
    CHECK (cost_effectiveness_rating BETWEEN 1 AND 5),
    CHECK (compliance_rating BETWEEN 1 AND 5)
);

CREATE INDEX idx_vendor_reviews_vendor ON vendor_performance_reviews(vendor_id);

-- Compliance Documents Table
CREATE TABLE IF NOT EXISTS vendor_compliance_documents (
    id VARCHAR(36) PRIMARY KEY,
    vendor_id VARCHAR(36) NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    document_name VARCHAR(255) NOT NULL,
    document_number VARCHAR(100),
    issue_date DATE,
    expiry_date DATE,
    issuing_authority VARCHAR(255),
    file_url VARCHAR(500) NOT NULL,
    file_name VARCHAR(255),
    file_size INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'valid',
    verification_status VARCHAR(50) DEFAULT 'pending',
    verified_by VARCHAR(36),
    verified_at TIMESTAMP,
    notes TEXT,
    uploaded_by VARCHAR(36) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    parent_document_id VARCHAR(36),
    
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
    FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_document_id) REFERENCES vendor_compliance_documents(id),
    CHECK (status IN ('valid', 'expiring_soon', 'expired', 'pending_review', 'rejected'))
);

CREATE INDEX idx_vendor_documents_vendor ON vendor_compliance_documents(vendor_id);
CREATE INDEX idx_vendor_documents_status ON vendor_compliance_documents(status);
CREATE INDEX idx_vendor_documents_expiry ON vendor_compliance_documents(expiry_date);

-- Communications Table
CREATE TABLE IF NOT EXISTS vendor_communications (
    id VARCHAR(36) PRIMARY KEY,
    vendor_id VARCHAR(36) NOT NULL,
    communication_type VARCHAR(50) NOT NULL,
    communication_date TIMESTAMP NOT NULL,
    subject VARCHAR(255) NOT NULL,
    details TEXT,
    attendees TEXT,
    outcome TEXT,
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    follow_up_notes TEXT,
    tags VARCHAR(255),
    attachment_urls TEXT,
    is_important BOOLEAN DEFAULT FALSE,
    logged_by VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
    FOREIGN KEY (logged_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_vendor_comms_vendor ON vendor_communications(vendor_id);
CREATE INDEX idx_vendor_comms_date ON vendor_communications(communication_date);

-- Notifications Table
CREATE TABLE IF NOT EXISTS vendor_notifications (
    id VARCHAR(36) PRIMARY KEY,
    vendor_id VARCHAR(36) NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    priority VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    action_required TEXT,
    deadline DATE,
    recipient_id VARCHAR(36) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    is_actioned BOOLEAN DEFAULT FALSE,
    actioned_at TIMESTAMP,
    related_entity_type VARCHAR(50),
    related_entity_id VARCHAR(36),
    sent_via_email BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_vendor_notifications_recipient ON vendor_notifications(recipient_id);
CREATE INDEX idx_vendor_notifications_read ON vendor_notifications(is_read);

-- Job Assignments Table
CREATE TABLE IF NOT EXISTS vendor_job_assignments (
    id VARCHAR(36) PRIMARY KEY,
    vendor_id VARCHAR(36) NOT NULL,
    job_id VARCHAR(36) NOT NULL,
    contract_id VARCHAR(36),
    assignment_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    fee_structure VARCHAR(100),
    fee_amount DECIMAL(15,2),
    candidates_submitted INTEGER DEFAULT 0,
    candidates_hired INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (contract_id) REFERENCES vendor_contracts(id) ON DELETE SET NULL,
    CHECK (status IN ('active', 'completed', 'cancelled'))
);

CREATE INDEX idx_vendor_jobs_vendor ON vendor_job_assignments(vendor_id);
CREATE INDEX idx_vendor_jobs_job ON vendor_job_assignments(job_id);

-- Analytics Table
CREATE TABLE IF NOT EXISTS vendor_analytics (
    id VARCHAR(36) PRIMARY KEY,
    vendor_id VARCHAR(36) NOT NULL,
    date DATE NOT NULL,
    total_jobs_assigned INTEGER DEFAULT 0,
    active_jobs INTEGER DEFAULT 0,
    candidates_submitted INTEGER DEFAULT 0,
    candidates_interviewed INTEGER DEFAULT 0,
    candidates_hired INTEGER DEFAULT 0,
    total_revenue DECIMAL(15,2) DEFAULT 0,
    average_rating DECIMAL(3,2),
    response_time_hours DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
    UNIQUE KEY unique_vendor_date (vendor_id, date)
);

CREATE INDEX idx_vendor_analytics_date ON vendor_analytics(date);
```

---

## 📦 Phase 2: Pydantic Schemas

**File**: `models/vendor_schemas.py`

```python
"""Pydantic schemas for vendor management"""
from pydantic import BaseModel, EmailStr, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from decimal import Decimal

# Enums
class VendorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_HOLD = "on-hold"
    BLACKLISTED = "blacklisted"

class ServiceCategory(str, Enum):
    RECRUITMENT = "Recruitment"
    TRAINING = "Training"
    STAFFING = "Staffing"
    CONSULTING = "Consulting"

class ContractStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"

# Base Schemas
class VendorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    service_category: ServiceCategory
    contact_person: Optional[str]
    contact_email: EmailStr
    contact_phone: Optional[str]
    website: Optional[HttpUrl]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    postal_code: Optional[str]
    tax_id: Optional[str]

class VendorCreate(VendorBase):
    vendor_manager_id: str

class VendorUpdate(BaseModel):
    name: Optional[str]
    contact_email: Optional[EmailStr]
    contact_phone: Optional[str]
    status: Optional[VendorStatus]
    vendor_manager_id: Optional[str]

class VendorResponse(VendorBase):
    id: str
    vendor_code: str
    status: VendorStatus
    overall_rating: Optional[Decimal]
    total_contracts: int
    active_contracts: int
    compliance_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Contract Schemas
class ContractCreate(BaseModel):
    contract_number: str
    contract_type: str
    title: str
    start_date: date
    end_date: date
    contract_value: Optional[Decimal]
    
    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

class ContractResponse(BaseModel):
    id: str
    contract_number: str
    title: str
    status: ContractStatus
    start_date: date
    end_date: date
    days_until_expiry: int
    
    class Config:
        from_attributes = True

# Performance Review Schemas
class PerformanceReviewCreate(BaseModel):
    review_period: str
    service_quality_rating: int = Field(..., ge=1, le=5)
    timeliness_rating: int = Field(..., ge=1, le=5)
    communication_rating: int = Field(..., ge=1, le=5)
    cost_effectiveness_rating: int = Field(..., ge=1, le=5)
    compliance_rating: int = Field(..., ge=1, le=5)
    written_feedback: Optional[str]

class PerformanceReviewResponse(BaseModel):
    id: str
    review_period: str
    overall_rating: Decimal
    status: str
    review_date: date
    
    class Config:
        from_attributes = True
```

---

## 🎯 Phase 3: Service Layer

**File**: `services/vendor_management_service.py`

```python
"""Vendor management service"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from models.database import Vendor, User
from models.vendor_schemas import VendorCreate, VendorUpdate

logger = logging.getLogger(__name__)

class VendorManagementService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def generate_vendor_code(self) -> str:
        """Generate unique vendor code VEN-YYYY-XXXX"""
        year = datetime.now().year
        query = select(func.count(Vendor.id)).where(
            Vendor.vendor_code.like(f"VEN-{year}-%")
        )
        result = await self.db.execute(query)
        count = result.scalar() or 0
        return f"VEN-{year}-{(count + 1):04d}"
    
    async def create_vendor(self, data: VendorCreate, current_user: User) -> Vendor:
        """Create new vendor"""
        vendor_code = await self.generate_vendor_code()
        
        vendor = Vendor(
            vendor_code=vendor_code,
            name=data.name,
            service_category=data.service_category,
            contact_email=data.contact_email,
            vendor_manager_id=data.vendor_manager_id,
            created_by=current_user.id,
            status='active'
        )
        
        self.db.add(vendor)
        await self.db.commit()
        await self.db.refresh(vendor)
        return vendor
    
    async def list_vendors(
        self,
        status: Optional[str] = None,
        service_category: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """List vendors with filters"""
        query = select(Vendor)
        
        if status:
            query = query.where(Vendor.status == status)
        if service_category:
            query = query.where(Vendor.service_category == service_category)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()
        
        # Pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        vendors = result.scalars().all()
        
        return {
            "vendors": vendors,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }
        }
```

---

## 🌐 Phase 4: API Endpoints

**File**: `api/vendors.py`

```python
"""Vendor management API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.vendor_management_service import VendorManagementService
from models.vendor_schemas import *

router = APIRouter(prefix="/api/vendors", tags=["vendors"])

@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    data: VendorCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new vendor"""
    service = VendorManagementService(db)
    vendor = await service.create_vendor(data, current_user)
    return vendor

@router.get("", response_model=VendorListResponse)
async def list_vendors(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List vendors"""
    service = VendorManagementService(db)
    return await service.list_vendors(status=status, page=page, limit=limit)

@router.get("/{vendor_id}", response_model=VendorDetailResponse)
async def get_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get vendor details"""
    service = VendorManagementService(db)
    vendor = await service.get_vendor_by_id(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor
```

---

## 🎨 Phase 5: UI Templates

Create templates in `templates/vendors/`:
- `list.html` - Vendor listing with search/filter
- `create.html` - Vendor creation form
- `detail.html` - Vendor detail page with tabs
- `contracts.html` - Contract management
- `reviews.html` - Performance reviews

---

## ✅ Implementation Checklist

- [ ] Phase 1: Database migration
- [ ] Phase 2: Pydantic schemas
- [ ] Phase 3: Service layer
- [ ] Phase 4: API endpoints
- [ ] Phase 5: HTML templates
- [ ] Phase 6: Testing
- [ ] Phase 7: Documentation

---

**Next**: Follow PRD for detailed requirements and acceptance criteria.
