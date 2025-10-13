# MVP-1 Role-Based User Flows
**Created:** October 13, 2025  
**Purpose:** Define user journeys for HR, Admin, and Vendor roles

---

## Overview

This document details the complete user workflows for three primary roles:
1. **HR Manager** - Recruitment and candidate management
2. **Admin** - System administration and oversight
3. **Vendor** - External candidate submissions

Each role has specific permissions, accessible features, and workflows tailored to their responsibilities.

---

## 1. HR Manager Complete Workflow

See: `MVP-1_HR_FLOW_DETAILED.md` for comprehensive HR workflows including:
- Resume vetting process
- Candidate search and filtering
- Rating and evaluation
- Job matching
- Pipeline management
- Interview scheduling

**Key Responsibilities:**
- Screen and vet candidate resumes
- Match candidates to jobs
- Track recruitment pipeline
- Rate and evaluate candidates

**Feature Access:**
- ✅ Resume Vetting, Upload, Preview
- ✅ Candidate Search, Detail, Rating
- ✅ Candidate Tracking & Pipeline
- ✅ Job Viewing (assigned jobs)
- ✅ AI Match Results
- ❌ User, Client, Vendor Management
- ❌ System Settings

---

## 2. Admin Complete Workflow

See: `MVP-1_ADMIN_FLOW_DETAILED.md` for comprehensive admin workflows including:
- User management (CRUD, permissions, audit logs)
- Client management (onboarding, subscriptions, metrics)
- Vendor management (contracts, performance tracking)
- System configuration and monitoring

**Key Responsibilities:**
- Manage all users, clients, and vendors
- Oversee all recruitment operations
- System configuration
- Generate system-wide reports

**Feature Access:**
- ✅ All HR features (full access)
- ✅ User Management (full CRUD)
- ✅ Client Management (full CRUD)
- ✅ Vendor Management (full CRUD)
- ✅ System Settings & Configuration
- ✅ Audit Logs & Analytics

---

## 3. Vendor Complete Workflow

See: `MVP-1_VENDOR_FLOW_DETAILED.md` for comprehensive vendor workflows including:
- Browse available job openings
- Submit candidates for jobs
- Track submission status
- View performance metrics

**Key Responsibilities:**
- Submit qualified candidates
- Track candidate progress
- Maintain high quality submissions
- Meet client expectations

**Feature Access:**
- ✅ Job Viewing (assigned/public jobs only)
- ✅ Resume Upload (for specific jobs)
- ✅ Own Submissions Tracking
- ✅ Performance Dashboard
- ❌ Full Candidate Database
- ❌ User/Client/Vendor Management

---

## Quick Reference: Feature Access Matrix

| Feature | HR Manager | Admin | Vendor |
|---------|-----------|-------|--------|
| **Resume Vetting** | ✅ Full | ✅ Full | ❌ |
| **Resume Upload** | ✅ Full | ✅ Full | ✅ For jobs only |
| **Candidate Search** | ✅ Full | ✅ Full | ❌ |
| **Candidate Detail** | ✅ View | ✅ Full | ✅ Own submissions |
| **Candidate Rating** | ✅ Full | ✅ Full | ❌ |
| **Candidate Tracking** | ✅ Assigned | ✅ All | ✅ Own submissions |
| **Job Viewing** | ✅ Assigned | ✅ All | ✅ Available only |
| **Job Creation** | ❌ | ✅ Full | ❌ |
| **AI Matching** | ✅ View | ✅ Full | ✅ At submission |
| **User Management** | ❌ | ✅ Full | ❌ |
| **Client Management** | 👁️ View | ✅ Full | ❌ |
| **Vendor Management** | 👁️ View | ✅ Full | 👁️ Own profile |
| **System Settings** | ❌ | ✅ Full | ❌ |
| **Audit Logs** | 👁️ Own | ✅ All | 👁️ Own |
| **Reports** | ✅ Own data | ✅ All | ✅ Own performance |

Legend: ✅ Full Access | 👁️ View Only | ❌ No Access

---

## Role-Specific Dashboards

### HR Manager Dashboard
- Pending reviews count
- Active jobs count
- Recent candidates
- Upcoming interviews
- Quick actions

### Admin Dashboard  
- System metrics (users, clients, vendors, jobs)
- Recent system activity
- System health monitoring
- Quick admin actions
- Audit log summary

### Vendor Dashboard
- Submission metrics (submitted, accepted, hired)
- Success rate and commission
- Available jobs list
- Recent submissions status
- Performance trends

---

## Navigation Structure

### Unified Navbar (Role-Based Visibility)

```
🤖 AI Powered HR Assistant
├─ Dashboard (All)
├─ Vetting (HR, Admin)
├─ Candidates (HR, Admin)
├─ Jobs (All)
├─ Clients (Admin only)
├─ Vendors (Admin only)
├─ Users (Admin only)
└─ [User Menu]
    ├─ Profile (All)
    ├─ Settings (All)
    └─ Logout (All)
```

For detailed workflows, refer to role-specific documentation:
- `MVP-1_HR_FLOW_DETAILED.md`
- `MVP-1_ADMIN_FLOW_DETAILED.md`
- `MVP-1_VENDOR_FLOW_DETAILED.md`
