# Implementation Plan: Client & Vendor Management

## Overview
This document outlines the comprehensive plan for implementing Client Management and Vendor Management features.

---

## Phase 1: Client Management

### 1.1 Database Layer (30 min)

#### Client Model Schema
```python
class Client(Base):
    __tablename__ = "clients"
    
    # Primary Key
    id = UUID (primary key)
    
    # Company Information
    company_name = String (required, unique)
    industry = String (optional)
    website = String (optional)
    description = Text (optional)
    
    # Contact Information
    contact_person = String (required)
    contact_email = String (required)
    contact_phone = String (optional)
    
    # Address
    address = String (optional)
    city = String (optional)
    state = String (optional)
    country = String (optional)
    postal_code = String (optional)
    
    # Business Details
    status = Enum('active', 'inactive', 'on_hold') default='active'
    client_type = Enum('direct', 'agency', 'partner') default='direct'
    priority = Enum('low', 'medium', 'high') default='medium'
    
    # Contract/Agreement
    contract_start_date = Date (optional)
    contract_end_date = Date (optional)
    contract_value = Decimal (optional)
    payment_terms = String (optional)
    
    # Notes & Tags
    notes = Text (optional)
    tags = JSON (optional) - array of strings
    
    # Metadata
    created_at = DateTime (auto)
    updated_at = DateTime (auto)
    created_by = UUID (foreign key to users)
    is_deleted = Boolean (default False)
    deleted_at = DateTime (nullable)
    deleted_by = UUID (nullable)
    
    # Relationships
    jobs = relationship("Job", back_populates="client")
```

#### Job Model Update
```python
# Add to existing Job model
client_id = UUID (foreign key to clients, nullable)
show_client_to_candidate = Boolean (default False)
client = relationship("Client", back_populates="jobs")
```

**Files to Create/Modify**:
- `models/database.py` - Add Client model
- `migrations/add_clients.py` - Migration script
- Update Job model with client relationship

---

### 1.2 Backend API Layer (45 min)

#### Endpoints to Create

**Client CRUD**:
- `POST /api/v1/clients` - Create new client
- `GET /api/v1/clients` - List all clients (with pagination, search, filter)
- `GET /api/v1/clients/{id}` - Get client details
- `PUT /api/v1/clients/{id}` - Update client
- `DELETE /api/v1/clients/{id}` - Soft delete client
- `GET /api/v1/clients/filter-options` - Get filter options

**Client Jobs**:
- `GET /api/v1/clients/{id}/jobs` - Get all jobs for a client
- `GET /api/v1/clients/{id}/stats` - Get client statistics

**Files to Create**:
- `api/v1/clients.py` - Client API router
- `services/client_service.py` - Client business logic
- `models/client_models.py` - Pydantic models for API

**Service Methods**:
```python
class ClientService:
    - create_client()
    - get_client_by_id()
    - update_client()
    - soft_delete_client()
    - list_clients() - with filters
    - search_clients()
    - get_client_stats()
    - get_client_jobs()
```

---

### 1.3 Frontend UI Layer (2 hours)

#### Pages to Create

**1. Clients List Page** (`/clients`)
- **Location**: `templates/clients/list.html`
- **Features**:
  - Data table with columns: Company, Contact Person, Email, Phone, Status, Created Date
  - Search bar (company name, contact person, email)
  - Filters: Status, Client Type, Priority
  - Sort by: Name, Created Date, Status
  - Actions: View, Edit, Delete
  - Add Client button (opens modal)
  - Export to CSV
  - Pagination

**2. Add/Edit Client Modal**
- **Location**: Component in `list.html`
- **Tabs**:
  - **Company Info**: Company name, industry, website, description
  - **Contact**: Contact person, email, phone
  - **Address**: Full address fields
  - **Business**: Status, type, priority, contract dates, value
  - **Notes**: Notes field, tags
- **Validation**: Required fields, email format, phone format
- **Actions**: Save, Cancel

**3. Client Detail Page** (`/clients/{id}`)
- **Location**: `templates/clients/detail.html`
- **Sections**:
  - **Header**: Company name, status badge, actions (Edit, Delete)
  - **Overview Card**: All client information in grid layout
  - **Jobs Section**: List of all jobs for this client (table)
  - **Statistics**: Total jobs, active jobs, filled positions
  - **Activity Timeline**: Recent activities related to client

**4. Update Job Pages**
- **Add to Job Create/Edit Form**: 
  - Client dropdown (optional, searchable)
  - "Show client to candidates" checkbox
- **Job Detail Page**:
  - Show client info (if exists and user has permission)
  - For candidates: Show only if `show_client_to_candidate` is true

**Files to Create**:
- `templates/clients/list.html`
- `templates/clients/detail.html`
- `static/css/clients.css` (if needed)
- `static/js/clients.js`

**Routes to Add** (in `main.py`):
- `/clients` - List page
- `/clients/{id}` - Detail page

---

### 1.4 Navigation Integration (15 min)

**Update Unified Navbar**:
- Add "Clients" link in main navigation
- Icon: `<i class="bi bi-building"></i>`
- Position: Between "Jobs" and "Vendors"

**Files to Modify**:
- `templates/components/unified_navbar.html`

---

## Phase 2: Vendor Management

### 2.1 Database Layer (30 min)

#### Vendor Model Schema
```python
class Vendor(Base):
    __tablename__ = "vendors"
    
    # Primary Key
    id = UUID (primary key)
    
    # Company Information
    vendor_name = String (required, unique)
    vendor_type = Enum('staffing', 'recruitment', 'consulting') default='recruitment'
    services_offered = JSON (array of strings)
    website = String (optional)
    description = Text (optional)
    
    # Contact Information
    contact_person = String (required)
    contact_email = String (required)
    contact_phone = String (optional)
    
    # Address
    address = String (optional)
    city = String (optional)
    state = String (optional)
    country = String (optional)
    postal_code = String (optional)
    
    # Business Details
    status = Enum('active', 'inactive', 'blacklisted') default='active'
    rating = Decimal (0-5 scale, optional)
    
    # Financial
    commission_rate = Decimal (percentage, optional)
    payment_terms = String (optional)
    rate_card = JSON (optional) - structured rate information
    
    # Performance Metrics
    total_placements = Integer (default 0)
    successful_placements = Integer (default 0)
    average_time_to_fill = Integer (days, optional)
    
    # Notes & Tags
    notes = Text (optional)
    tags = JSON (optional)
    
    # Metadata
    created_at = DateTime (auto)
    updated_at = DateTime (auto)
    created_by = UUID (foreign key to users)
    is_deleted = Boolean (default False)
    deleted_at = DateTime (nullable)
    deleted_by = UUID (nullable)
    
    # Relationships
    candidates = relationship("CandidateVendor", back_populates="vendor")
```

#### CandidateVendor Linking Table
```python
class CandidateVendor(Base):
    __tablename__ = "candidate_vendors"
    
    id = UUID (primary key)
    candidate_id = UUID (foreign key to candidates)
    vendor_id = UUID (foreign key to vendors)
    
    # Sourcing Details
    sourced_date = Date (auto)
    placement_fee = Decimal (optional)
    guarantee_period_days = Integer (optional)
    
    # Status
    status = Enum('sourced', 'submitted', 'interviewed', 'placed', 'rejected')
    notes = Text (optional)
    
    # Metadata
    created_at = DateTime (auto)
    updated_at = DateTime (auto)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="vendors")
    vendor = relationship("Vendor", back_populates="candidates")
```

#### Candidate Model Update
```python
# Add to existing Candidate model
vendors = relationship("CandidateVendor", back_populates="candidate")
```

**Files to Create/Modify**:
- `models/database.py` - Add Vendor and CandidateVendor models
- `migrations/add_vendors.py` - Migration script
- Update Candidate model with vendor relationship

---

### 2.2 Backend API Layer (45 min)

#### Endpoints to Create

**Vendor CRUD**:
- `POST /api/v1/vendors` - Create new vendor
- `GET /api/v1/vendors` - List all vendors (with pagination, search, filter)
- `GET /api/v1/vendors/{id}` - Get vendor details
- `PUT /api/v1/vendors/{id}` - Update vendor
- `DELETE /api/v1/vendors/{id}` - Soft delete vendor
- `GET /api/v1/vendors/filter-options` - Get filter options

**Vendor Candidates**:
- `GET /api/v1/vendors/{id}/candidates` - Get all candidates from vendor
- `POST /api/v1/vendors/{id}/candidates` - Link candidate to vendor
- `DELETE /api/v1/vendors/{id}/candidates/{candidate_id}` - Unlink candidate
- `GET /api/v1/vendors/{id}/stats` - Get vendor statistics
- `PUT /api/v1/vendors/{id}/performance` - Update performance metrics

**Candidate Vendor Info**:
- `GET /api/v1/candidates/{id}/vendors` - Get vendors for a candidate
- `POST /api/v1/candidates/{id}/vendors` - Link vendor to candidate

**Files to Create**:
- `api/v1/vendors.py` - Vendor API router
- `services/vendor_service.py` - Vendor business logic
- `models/vendor_models.py` - Pydantic models for API

**Service Methods**:
```python
class VendorService:
    - create_vendor()
    - get_vendor_by_id()
    - update_vendor()
    - soft_delete_vendor()
    - list_vendors() - with filters
    - search_vendors()
    - get_vendor_stats()
    - get_vendor_candidates()
    - link_candidate_to_vendor()
    - unlink_candidate_from_vendor()
    - update_vendor_performance()
```

---

### 2.3 Frontend UI Layer (2 hours)

#### Pages to Create

**1. Vendors List Page** (`/vendors`)
- **Location**: `templates/vendors/list.html`
- **Features**:
  - Data table: Vendor Name, Type, Contact, Phone, Status, Rating, Placements
  - Search bar (vendor name, contact person, email)
  - Filters: Status, Vendor Type, Rating
  - Sort by: Name, Rating, Placements, Created Date
  - Actions: View, Edit, Delete
  - Add Vendor button (opens modal)
  - Export to CSV
  - Pagination

**2. Add/Edit Vendor Modal**
- **Location**: Component in `list.html`
- **Tabs**:
  - **Company Info**: Vendor name, type, services, website, description
  - **Contact**: Contact person, email, phone
  - **Address**: Full address fields
  - **Business**: Status, commission rate, payment terms
  - **Performance**: Rating, placements, time-to-fill
  - **Notes**: Notes field, tags
- **Validation**: Required fields, email format, phone format
- **Actions**: Save, Cancel

**3. Vendor Detail Page** (`/vendors/{id}`)
- **Location**: `templates/vendors/detail.html`
- **Sections**:
  - **Header**: Vendor name, status badge, rating, actions (Edit, Delete)
  - **Overview Card**: All vendor information in grid layout
  - **Performance Metrics**: Visual charts for placements, success rate, time-to-fill
  - **Candidates Section**: List of candidates sourced by this vendor (table)
  - **Activity Timeline**: Recent activities related to vendor

**4. Update Candidate Pages**
- **Candidate Detail Page**:
  - Add "Vendor Source" section showing which vendor sourced the candidate
  - Button to link/unlink vendor
- **Vetting Page**:
  - Optional dropdown to assign vendor during vetting

**Files to Create**:
- `templates/vendors/list.html`
- `templates/vendors/detail.html`
- `static/css/vendors.css` (if needed)
- `static/js/vendors.js`

**Routes to Add** (in `main.py`):
- `/vendors` - List page
- `/vendors/{id}` - Detail page

---

### 2.4 Navigation Integration (15 min)

**Update Unified Navbar**:
- Add "Vendors" link in main navigation
- Icon: `<i class="bi bi-shop"></i>`
- Position: Between "Clients" and "Users"

**Files to Modify**:
- `templates/components/unified_navbar.html`

---

## Phase 3: Integration & Testing

### 3.1 Job-Client Integration (30 min)
- Update job creation form with client dropdown
- Update job detail page to show client (with permissions)
- Add client visibility toggle
- Test job-client linking

### 3.2 Candidate-Vendor Integration (30 min)
- Update candidate detail page with vendor section
- Add vendor assignment during vetting
- Test candidate-vendor linking
- Test vendor performance tracking

### 3.3 Reporting & Analytics (1 hour)
- Client dashboard with metrics
- Vendor dashboard with performance
- Export functionality
- Activity logs

---

## Implementation Timeline

### Day 1: Client Management (4-5 hours)
- ✅ Database models and migration (30 min)
- ✅ Backend API endpoints (45 min)
- ✅ Client list page (1 hour)
- ✅ Add/Edit client modal (45 min)
- ✅ Client detail page (1 hour)
- ✅ Job integration (30 min)
- ✅ Testing (30 min)

### Day 2: Vendor Management (4-5 hours)
- ✅ Database models and migration (30 min)
- ✅ Backend API endpoints (45 min)
- ✅ Vendor list page (1 hour)
- ✅ Add/Edit vendor modal (45 min)
- ✅ Vendor detail page (1 hour)
- ✅ Candidate integration (30 min)
- ✅ Testing (30 min)

### Day 3: Polish & Integration (2-3 hours)
- ✅ Navigation integration (15 min)
- ✅ Permissions and security (30 min)
- ✅ UI polish and responsiveness (1 hour)
- ✅ End-to-end testing (1 hour)
- ✅ Documentation (30 min)

---

## Technical Considerations

### Design System
- Use existing unified styles (`unified_styles.css`)
- Match color scheme: Primary blue (#0d6efd)
- Consistent card layouts
- Bootstrap 5.3 components
- Bootstrap Icons

### Responsive Design
- Mobile-first approach
- Collapsible sidebar on mobile
- Responsive tables (horizontal scroll if needed)
- Touch-friendly buttons

### Performance
- Pagination for large datasets (20 items per page)
- Lazy loading for detail pages
- Efficient database queries with eager loading
- Caching for frequently accessed data

### Security
- User authentication required
- Role-based access control (if applicable)
- Input validation on frontend and backend
- SQL injection prevention (using SQLAlchemy ORM)
- XSS prevention (escaping HTML)

### Testing Strategy
- Manual testing of all CRUD operations
- Test search and filter functionality
- Test linking (jobs-clients, candidates-vendors)
- Test soft delete and restore
- Test permissions and visibility controls

---

## Success Criteria

### Client Management
- ✅ Can create, edit, and delete clients
- ✅ Can search and filter clients
- ✅ Can view client details with all jobs
- ✅ Can link jobs to clients (optional)
- ✅ Can control client visibility to candidates
- ✅ UI is responsive and matches existing design

### Vendor Management
- ✅ Can create, edit, and delete vendors
- ✅ Can search and filter vendors
- ✅ Can view vendor details with performance metrics
- ✅ Can link candidates to vendors
- ✅ Can track vendor performance
- ✅ UI is responsive and matches existing design

---

## Files Summary

### New Files to Create (20+ files)
**Backend**:
1. `models/client_models.py`
2. `models/vendor_models.py`
3. `api/v1/clients.py`
4. `api/v1/vendors.py`
5. `services/client_service.py`
6. `services/vendor_service.py`
7. `migrations/add_clients.py`
8. `migrations/add_vendors.py`

**Frontend**:
9. `templates/clients/list.html`
10. `templates/clients/detail.html`
11. `templates/vendors/list.html`
12. `templates/vendors/detail.html`
13. `static/js/clients.js`
14. `static/js/vendors.js`
15. `static/css/clients.css` (optional)
16. `static/css/vendors.css` (optional)

### Files to Modify (5+ files)
1. `models/database.py` - Add Client, Vendor, CandidateVendor models
2. `main.py` - Add new routers and routes
3. `templates/components/unified_navbar.html` - Add navigation links
4. `templates/jobs/create.html` - Add client dropdown
5. `templates/jobs/detail.html` - Show client info
6. `templates/candidate_detail.html` - Add vendor section

---

## Next Steps

1. **Review and Approve** this plan
2. **Start with Client Management** (Phase 1)
3. **Move to Vendor Management** (Phase 2)
4. **Integration and Polish** (Phase 3)

Ready to begin implementation! 🚀
