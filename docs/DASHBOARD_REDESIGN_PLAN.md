# Dashboard Redesign Plan
**Date:** October 13, 2025  
**Purpose:** Transform landing page into functional role-based dashboard

---

## 🎯 Problem Statement

### Current Issues
1. **Landing page, not dashboard** - Hero section with marketing copy
2. **Redundant cards** - First 3 cards (Vetting, Authenticity, JD Matching) all go to `/vet-resumes`
3. **Not role-specific** - Shows all features to all users
4. **No actionable data** - No metrics, stats, or quick actions
5. **Poor information hierarchy** - Feature descriptions instead of actual data

### User Needs
- **HR Managers:** Quick access to pending tasks, recent candidates, job stats
- **Admins:** System overview, user activity, performance metrics
- **Vendors:** Available jobs, submission status, performance

---

## 🎨 Proposed Solution

### Two-Page Approach

#### 1. Landing Page (`/` - Not Logged In)
**Purpose:** Marketing/welcome page for non-authenticated users  
**Location:** Keep current design or create new `templates/landing.html`  
**Content:**
- Hero section with value proposition
- Feature highlights
- Call-to-action (Login/Sign Up)
- How it works section

#### 2. Dashboard (`/` or `/dashboard` - Logged In)
**Purpose:** Role-based functional dashboard  
**Location:** `templates/dashboards/` (role-specific)  
**Content:**
- Real-time metrics and KPIs
- Quick actions
- Recent activity
- Pending tasks
- Role-specific widgets

---

## 📊 Dashboard Designs by Role

### HR Manager Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  🤖 AI Powered HR Assistant                    [User Menu]  │
└─────────────────────────────────────────────────────────────┘

┌─ HR Dashboard ──────────────────────────────────────────────┐
│                                                              │
│  📊 Quick Stats                                              │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐ │
│  │📄 Candidates │🔍 Pending    │✅ Shortlisted│💼 Active  │ │
│  │     245      │  Vetting: 12 │      38      │  Jobs: 8  │ │
│  └──────────────┴──────────────┴──────────────┴───────────┘ │
│                                                              │
│  ⚡ Quick Actions                                            │
│  [🛡️ Vet Resumes] [📤 Upload Resume] [🔍 Search Candidates] │
│                                                              │
│  ┌─ Pending Vetting (12) ──────────┬─ Recent Candidates ──┐ │
│  │                                  │                       │ │
│  │ • John Doe - Software Engineer   │ • Jane Smith         │ │
│  │   Uploaded: 2 hours ago          │   Score: 92%         │ │
│  │   [Review]                       │   Status: Shortlist  │ │
│  │                                  │                       │ │
│  │ • Sarah Johnson - Data Analyst   │ • Mike Chen          │ │
│  │   Uploaded: 5 hours ago          │   Score: 88%         │ │
│  │   [Review]                       │   Status: Interview  │ │
│  │                                  │                       │ │
│  │ [View All Pending →]             │ [View All →]         │ │
│  └──────────────────────────────────┴──────────────────────┘ │
│                                                              │
│  ┌─ Active Jobs (8) ────────────────┬─ Recent Activity ───┐ │
│  │                                  │                       │ │
│  │ • Senior Java Developer          │ • 3 new candidates   │ │
│  │   Candidates: 24 | Open: 15 days │   for Java Dev       │ │
│  │   [View Details]                 │   2 min ago          │ │
│  │                                  │                       │ │
│  │ • UI/UX Designer                 │ • Vetting completed  │ │
│  │   Candidates: 18 | Open: 8 days  │   for 5 resumes      │ │
│  │   [View Details]                 │   1 hour ago         │ │
│  │                                  │                       │ │
│  │ [View All Jobs →]                │ [View All →]         │ │
│  └──────────────────────────────────┴──────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Key Widgets:**
1. **Quick Stats Cards** - At-a-glance metrics
2. **Quick Actions** - Primary workflows (Vet, Upload, Search)
3. **Pending Vetting Queue** - Resumes awaiting review
4. **Recent Candidates** - Latest additions with scores
5. **Active Jobs** - Current openings with candidate counts
6. **Recent Activity** - Timeline of recent actions

---

### Admin Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  🤖 AI Powered HR Assistant                    [User Menu]  │
└─────────────────────────────────────────────────────────────┘

┌─ Admin Dashboard ───────────────────────────────────────────┐
│                                                              │
│  📊 System Overview                                          │
│  ┌──────────┬──────────┬──────────┬──────────┬───────────┐  │
│  │👥 Users  │💼 Jobs   │📄 Resumes│✅ Vetted │📈 Today   │  │
│  │   45     │   23     │   1,245  │   892    │  +12      │  │
│  └──────────┴──────────┴──────────┴──────────┴───────────┘  │
│                                                              │
│  ⚡ Admin Actions                                            │
│  [👤 Manage Users] [💼 Manage Jobs] [📊 View Analytics]     │
│                                                              │
│  ┌─ User Activity (Last 24h) ─────┬─ System Health ───────┐ │
│  │                                 │                        │ │
│  │ 📈 Active Users: 28             │ ✅ All Systems OK      │ │
│  │ 📤 Uploads: 45                  │ 🗄️ Database: Healthy  │ │
│  │ 🔍 Searches: 123                │ 🚀 API: Responsive    │ │
│  │ 🛡️ Vetting Sessions: 8          │ 💾 Storage: 45% used  │ │
│  │                                 │                        │ │
│  │ [View Detailed Analytics →]     │ [View Logs →]         │ │
│  └─────────────────────────────────┴───────────────────────┘ │
│                                                              │
│  ┌─ Recent Users ──────────────────┬─ Performance Metrics ─┐ │
│  │                                 │                        │ │
│  │ • Sarah (HR) - Active now       │ Avg Vetting Time:     │ │
│  │ • Mike (HR) - 2 hours ago       │   3.5 minutes         │ │
│  │ • John (Admin) - 5 hours ago    │                        │ │
│  │                                 │ Match Accuracy:       │ │
│  │ [Manage All Users →]            │   94.2%               │ │
│  │                                 │                        │ │
│  │                                 │ [View Full Report →]  │ │
│  └─────────────────────────────────┴───────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Key Widgets:**
1. **System Overview** - High-level metrics
2. **Admin Actions** - Management functions
3. **User Activity** - Real-time usage stats
4. **System Health** - Status indicators
5. **Recent Users** - User activity log
6. **Performance Metrics** - System performance

---

### Vendor Dashboard (Future)

```
┌─────────────────────────────────────────────────────────────┐
│  🤖 AI Powered HR Assistant                    [User Menu]  │
└─────────────────────────────────────────────────────────────┘

┌─ Vendor Dashboard ──────────────────────────────────────────┐
│                                                              │
│  📊 My Performance                                           │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐ │
│  │📤 Submitted  │✅ Accepted   │🎯 Hired      │⭐ Rating  │ │
│  │     45       │      35      │      8       │  4.5/5    │ │
│  └──────────────┴──────────────┴──────────────┴───────────┘ │
│                                                              │
│  ⚡ Quick Actions                                            │
│  [💼 Browse Jobs] [📤 Submit Candidate] [📊 My Submissions] │
│                                                              │
│  ┌─ Available Jobs (12) ────────┬─ My Recent Submissions ─┐ │
│  │                               │                          │ │
│  │ • Senior Java Developer       │ • John Doe → TechCorp   │ │
│  │   TechCorp Inc.               │   Status: Shortlisted   │ │
│  │   Commission: 15%             │   Submitted: 2 days ago │ │
│  │   [Submit Candidate]          │                          │ │
│  │                               │ • Jane Smith → StartupX │ │
│  │ • UI/UX Designer              │   Status: Interviewed   │ │
│  │   StartupXYZ                  │   Submitted: 5 days ago │ │
│  │   Commission: 12%             │                          │ │
│  │   [Submit Candidate]          │ [View All →]            │ │
│  │                               │                          │ │
│  │ [View All Jobs →]             │                          │ │
│  └───────────────────────────────┴─────────────────────────┘ │
│                                                              │
│  ┌─ Commission Summary ──────────────────────────────────── │
│  │ Pending: $12,500 | Approved: $8,000 | Paid: $24,500     │ │
│  │ [View Details →]                                         │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Implementation Plan

### Phase 1: Create Dashboard Templates (Week 1)

#### Step 1: Create Dashboard Directory Structure
```
templates/
├── dashboards/
│   ├── hr_dashboard.html          # HR Manager dashboard
│   ├── admin_dashboard.html       # Admin dashboard
│   ├── vendor_dashboard.html      # Vendor dashboard (future)
│   └── components/
│       ├── stats_card.html        # Reusable stat card
│       ├── quick_actions.html     # Quick action buttons
│       ├── activity_feed.html     # Activity timeline
│       └── widget_card.html       # Generic widget container
├── landing.html                    # New landing page (optional)
└── index.html                      # Current (to be replaced or redirected)
```

#### Step 2: Create Backend Dashboard APIs
```python
# api/v1/dashboard.py

@router.get("/dashboard/hr")
async def get_hr_dashboard_data(user: User = Depends(get_current_user)):
    """Get HR dashboard data"""
    return {
        "stats": {
            "total_candidates": 245,
            "pending_vetting": 12,
            "shortlisted": 38,
            "active_jobs": 8
        },
        "pending_vetting": [...],  # List of pending resumes
        "recent_candidates": [...],  # Recent additions
        "active_jobs": [...],  # Current openings
        "recent_activity": [...]  # Activity timeline
    }

@router.get("/dashboard/admin")
async def get_admin_dashboard_data(user: User = Depends(get_current_user)):
    """Get admin dashboard data"""
    return {
        "stats": {
            "total_users": 45,
            "total_jobs": 23,
            "total_resumes": 1245,
            "vetted_resumes": 892,
            "today_uploads": 12
        },
        "user_activity": {...},
        "system_health": {...},
        "recent_users": [...],
        "performance_metrics": {...}
    }
```

#### Step 3: Update Routing Logic
```python
# main.py

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Route to appropriate page based on auth status"""
    user = await get_current_user(request)
    
    if not user:
        # Not logged in - show landing page
        return templates.TemplateResponse("landing.html", {"request": request})
    
    # Logged in - route to role-specific dashboard
    if user.role == "admin":
        return templates.TemplateResponse("dashboards/admin_dashboard.html", 
                                         {"request": request, "user": user})
    elif user.role == "hr":
        return templates.TemplateResponse("dashboards/hr_dashboard.html", 
                                         {"request": request, "user": user})
    elif user.role == "vendor":
        return templates.TemplateResponse("dashboards/vendor_dashboard.html", 
                                         {"request": request, "user": user})
    else:
        # Default dashboard
        return templates.TemplateResponse("dashboards/hr_dashboard.html", 
                                         {"request": request, "user": user})
```

---

### Phase 2: Build Dashboard Components (Week 1-2)

#### Component 1: Stats Card Widget
```html
<!-- templates/dashboards/components/stats_card.html -->
<div class="col-md-3">
    <div class="card stat-card">
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="text-muted mb-1">{{ title }}</h6>
                    <h2 class="mb-0">{{ value }}</h2>
                    {% if subtitle %}
                    <small class="text-muted">{{ subtitle }}</small>
                    {% endif %}
                </div>
                <div class="stat-icon">
                    <i class="bi bi-{{ icon }}"></i>
                </div>
            </div>
        </div>
    </div>
</div>
```

#### Component 2: Quick Actions
```html
<!-- templates/dashboards/components/quick_actions.html -->
<div class="quick-actions mb-4">
    <h5 class="mb-3">⚡ Quick Actions</h5>
    <div class="d-flex gap-2 flex-wrap">
        {% for action in actions %}
        <a href="{{ action.url }}" class="btn btn-{{ action.style }}">
            <i class="bi bi-{{ action.icon }}"></i> {{ action.label }}
        </a>
        {% endfor %}
    </div>
</div>
```

#### Component 3: Widget Card
```html
<!-- templates/dashboards/components/widget_card.html -->
<div class="col-md-6">
    <div class="card widget-card h-100">
        <div class="card-header d-flex justify-content-between align-items-center">
            <h6 class="mb-0">{{ title }}</h6>
            {% if action_url %}
            <a href="{{ action_url }}" class="btn btn-sm btn-link">{{ action_text }} →</a>
            {% endif %}
        </div>
        <div class="card-body">
            {{ content }}
        </div>
    </div>
</div>
```

---

### Phase 3: Implement HR Dashboard (Week 2)

#### HR Dashboard Template
```html
<!-- templates/dashboards/hr_dashboard.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - AI Powered HR Assistant</title>
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <link rel="stylesheet" href="/static/css/unified_styles.css">
    <link rel="stylesheet" href="/static/css/dashboard.css">
</head>
<body>
    {% include 'components/unified_navbar.html' %}
    
    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <h2 class="mb-4">HR Dashboard</h2>
                
                <!-- Quick Stats -->
                <div class="row mb-4" id="quickStats">
                    <!-- Stats cards loaded via API -->
                </div>
                
                <!-- Quick Actions -->
                <div class="quick-actions mb-4">
                    <h5 class="mb-3">⚡ Quick Actions</h5>
                    <div class="d-flex gap-2">
                        <a href="/vet-resumes" class="btn btn-primary">
                            <i class="bi bi-shield-check"></i> Vet Resumes
                        </a>
                        <a href="/upload" class="btn btn-outline-primary">
                            <i class="bi bi-cloud-upload"></i> Upload Resume
                        </a>
                        <a href="/candidates" class="btn btn-outline-primary">
                            <i class="bi bi-search"></i> Search Candidates
                        </a>
                    </div>
                </div>
                
                <!-- Dashboard Widgets -->
                <div class="row">
                    <!-- Pending Vetting -->
                    <div class="col-md-6 mb-4">
                        <div class="card widget-card">
                            <div class="card-header d-flex justify-content-between">
                                <h6 class="mb-0">🛡️ Pending Vetting (<span id="pendingCount">0</span>)</h6>
                                <a href="/vet-resumes" class="btn btn-sm btn-link">View All →</a>
                            </div>
                            <div class="card-body" id="pendingVetting">
                                <!-- Loaded via API -->
                            </div>
                        </div>
                    </div>
                    
                    <!-- Recent Candidates -->
                    <div class="col-md-6 mb-4">
                        <div class="card widget-card">
                            <div class="card-header d-flex justify-content-between">
                                <h6 class="mb-0">👥 Recent Candidates</h6>
                                <a href="/candidates" class="btn btn-sm btn-link">View All →</a>
                            </div>
                            <div class="card-body" id="recentCandidates">
                                <!-- Loaded via API -->
                            </div>
                        </div>
                    </div>
                    
                    <!-- Active Jobs -->
                    <div class="col-md-6 mb-4">
                        <div class="card widget-card">
                            <div class="card-header d-flex justify-content-between">
                                <h6 class="mb-0">💼 Active Jobs</h6>
                                <a href="/jobs" class="btn btn-sm btn-link">View All →</a>
                            </div>
                            <div class="card-body" id="activeJobs">
                                <!-- Loaded via API -->
                            </div>
                        </div>
                    </div>
                    
                    <!-- Recent Activity -->
                    <div class="col-md-6 mb-4">
                        <div class="card widget-card">
                            <div class="card-header">
                                <h6 class="mb-0">📊 Recent Activity</h6>
                            </div>
                            <div class="card-body" id="recentActivity">
                                <!-- Loaded via API -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/dashboard.js"></script>
</body>
</html>
```

---

### Phase 4: Dashboard Styling (Week 2)

#### Dashboard-Specific CSS
```css
/* static/css/dashboard.css */

/* Stat Cards */
.stat-card {
    border-left: 4px solid var(--primary-solid);
    transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.stat-icon {
    font-size: 2.5rem;
    color: var(--primary-solid);
    opacity: 0.3;
}

/* Widget Cards */
.widget-card {
    border: none;
    box-shadow: var(--shadow);
}

.widget-card .card-header {
    background: var(--surface);
    border-bottom: 2px solid var(--border-light);
    padding: 1rem 1.25rem;
}

/* Quick Actions */
.quick-actions {
    padding: 1.5rem;
    background: var(--surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow);
}

/* Activity Feed */
.activity-item {
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border-light);
}

.activity-item:last-child {
    border-bottom: none;
}

.activity-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--primary-light);
    color: white;
}

/* List Items */
.list-item {
    padding: 1rem;
    border-bottom: 1px solid var(--border-light);
    transition: background-color 0.2s;
}

.list-item:hover {
    background-color: var(--border-light);
}

.list-item:last-child {
    border-bottom: none;
}

/* Empty State */
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-secondary);
}

.empty-state i {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.3;
}
```

---

### Phase 5: Dashboard JavaScript (Week 2)

#### Dashboard Data Loading
```javascript
// static/js/dashboard.js

// Load dashboard data on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboardData();
    
    // Refresh every 5 minutes
    setInterval(loadDashboardData, 300000);
});

async function loadDashboardData() {
    try {
        const response = await fetch('/api/v1/dashboard/hr');
        const data = await response.json();
        
        renderQuickStats(data.stats);
        renderPendingVetting(data.pending_vetting);
        renderRecentCandidates(data.recent_candidates);
        renderActiveJobs(data.active_jobs);
        renderRecentActivity(data.recent_activity);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function renderQuickStats(stats) {
    const container = document.getElementById('quickStats');
    container.innerHTML = `
        <div class="col-md-3">
            <div class="card stat-card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-muted mb-1">Total Candidates</h6>
                            <h2 class="mb-0">${stats.total_candidates}</h2>
                        </div>
                        <div class="stat-icon">
                            <i class="bi bi-people-fill"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card stat-card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-muted mb-1">Pending Vetting</h6>
                            <h2 class="mb-0">${stats.pending_vetting}</h2>
                        </div>
                        <div class="stat-icon">
                            <i class="bi bi-shield-check"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card stat-card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-muted mb-1">Shortlisted</h6>
                            <h2 class="mb-0">${stats.shortlisted}</h2>
                        </div>
                        <div class="stat-icon">
                            <i class="bi bi-star-fill"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card stat-card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-muted mb-1">Active Jobs</h6>
                            <h2 class="mb-0">${stats.active_jobs}</h2>
                        </div>
                        <div class="stat-icon">
                            <i class="bi bi-briefcase-fill"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderPendingVetting(items) {
    const container = document.getElementById('pendingVetting');
    document.getElementById('pendingCount').textContent = items.length;
    
    if (items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-check-circle"></i>
                <p>No pending resumes to vet</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = items.map(item => `
        <div class="list-item">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-1">${item.name}</h6>
                    <small class="text-muted">
                        <i class="bi bi-clock"></i> ${item.uploaded_time}
                    </small>
                </div>
                <a href="/vet-resumes?resume=${item.id}" class="btn btn-sm btn-primary">
                    Review
                </a>
            </div>
        </div>
    `).join('');
}

// Similar functions for other widgets...
```

---

## 📋 Implementation Checklist

### Week 1: Foundation
- [ ] Create `templates/dashboards/` directory
- [ ] Create dashboard component templates
- [ ] Create `api/v1/dashboard.py` with endpoints
- [ ] Update routing logic in `main.py`
- [ ] Create `static/css/dashboard.css`
- [ ] Create `static/js/dashboard.js`

### Week 2: HR Dashboard
- [ ] Build HR dashboard template
- [ ] Implement dashboard data API
- [ ] Create widget components
- [ ] Add real-time data loading
- [ ] Test with real data
- [ ] Style and polish

### Week 3: Admin Dashboard
- [ ] Build admin dashboard template
- [ ] Implement admin data API
- [ ] Add system health monitoring
- [ ] Add user activity tracking
- [ ] Test and polish

### Week 4: Polish & Testing
- [ ] Responsive design testing
- [ ] Performance optimization
- [ ] Cross-browser testing
- [ ] User acceptance testing
- [ ] Documentation

---

## 🎯 Success Criteria

### Functional Requirements
- [ ] Role-based dashboard routing works
- [ ] Real-time data updates
- [ ] Quick actions functional
- [ ] All widgets display correctly
- [ ] Responsive on all devices

### User Experience
- [ ] Dashboard loads in < 2 seconds
- [ ] Clear information hierarchy
- [ ] Actionable insights
- [ ] Easy navigation to features
- [ ] Professional appearance

### Technical Requirements
- [ ] API endpoints performant
- [ ] Efficient database queries
- [ ] Proper error handling
- [ ] Secure data access
- [ ] Scalable architecture

---

## 💡 Recommendations

### Immediate Actions
1. **Keep current index.html as landing.html** - Preserve for non-authenticated users
2. **Create HR dashboard first** - Most common user type
3. **Use real data from start** - Don't mock, integrate with existing APIs
4. **Make it modular** - Reusable components for future dashboards

### Future Enhancements
1. **Customizable widgets** - Let users choose what to display
2. **Export capabilities** - Download dashboard data
3. **Notifications** - Real-time alerts for important events
4. **Dark mode** - Theme toggle
5. **Mobile app** - Progressive Web App (PWA)

---

**Next Steps:** Start with creating the dashboard directory structure and HR dashboard template, then implement the backend API endpoints.
