# MVP-1 UI/UX Unification Guide
**Created:** October 13, 2025  
**Purpose:** Standardize design system across the application

---

## 🎨 Design System

### Brand Identity

**Application Name:** AI Powered HR Assistant  
**Tagline:** "Intelligent Recruitment, Simplified"

**Logo/Icon:** 🤖 (Robot emoji - consistent across all pages)

### Color Palette

```css
/* Primary Colors */
--primary-gradient-start: #667eea;  /* Soft Purple */
--primary-gradient-end: #764ba2;    /* Deep Purple */
--primary-solid: #4F46E5;           /* Indigo */
--primary-hover: #4338CA;           /* Dark Indigo */

/* Secondary Colors */
--secondary-success: #10B981;       /* Green */
--secondary-warning: #F59E0B;       /* Amber */
--secondary-danger: #EF4444;        /* Red */
--secondary-info: #3B82F6;          /* Blue */

/* Neutral Colors */
--background: #F9FAFB;              /* Light Gray */
--surface: #FFFFFF;                 /* White */
--text-primary: #1F2937;            /* Dark Gray */
--text-secondary: #6B7280;          /* Medium Gray */
--text-tertiary: #9CA3AF;           /* Light Gray */
--border: #E5E7EB;                  /* Border Gray */

/* Status Colors */
--status-new: #3B82F6;              /* Blue */
--status-shortlisted: #F59E0B;      /* Amber */
--status-interviewed: #8B5CF6;      /* Purple */
--status-offered: #10B981;          /* Green */
--status-hired: #059669;            /* Dark Green */
--status-rejected: #EF4444;         /* Red */
```

### Typography

```css
/* Font Family */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Spacing

```css
/* Spacing Scale (4px base) */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

### Shadows

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
```

### Border Radius

```css
--radius-sm: 0.25rem;   /* 4px */
--radius: 0.375rem;     /* 6px */
--radius-md: 0.5rem;    /* 8px */
--radius-lg: 0.75rem;   /* 12px */
--radius-xl: 1rem;      /* 16px */
--radius-full: 9999px;  /* Fully rounded */
```

---

## 🧩 Component Library

### Unified Navigation Bar

**Location:** `templates/components/unified_navbar.html`

```html
<nav class="navbar navbar-expand-lg navbar-dark sticky-top" 
     style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
    <div class="container-fluid px-4">
        <!-- Brand -->
        <a class="navbar-brand fw-bold" href="/" style="font-size: 1.25rem;">
            <span style="font-size: 1.5rem;">🤖</span>
            AI Powered HR Assistant
        </a>
        
        <!-- Mobile Toggle -->
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" 
                data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        
        <!-- Navigation Links -->
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav me-auto">
                <!-- Dashboard (All Roles) -->
                <li class="nav-item">
                    <a class="nav-link {% if request.url.path == '/' %}active{% endif %}" 
                       href="/">
                        <i class="bi bi-house-door"></i> Dashboard
                    </a>
                </li>
                
                <!-- Vetting (HR & Admin) -->
                {% if user.role in ['hr', 'admin'] %}
                <li class="nav-item">
                    <a class="nav-link {% if 'vet' in request.url.path %}active{% endif %}" 
                       href="/vet-resumes">
                        <i class="bi bi-shield-check"></i> Vetting
                    </a>
                </li>
                {% endif %}
                
                <!-- Candidates (HR & Admin) -->
                {% if user.role in ['hr', 'admin'] %}
                <li class="nav-item">
                    <a class="nav-link {% if 'candidates' in request.url.path %}active{% endif %}" 
                       href="/candidates">
                        <i class="bi bi-people"></i> Candidates
                    </a>
                </li>
                {% endif %}
                
                <!-- Jobs (All Roles) -->
                <li class="nav-item">
                    <a class="nav-link {% if 'jobs' in request.url.path %}active{% endif %}" 
                       href="/jobs">
                        <i class="bi bi-briefcase"></i> Jobs
                    </a>
                </li>
                
                <!-- Clients (Admin Only) -->
                {% if user.role == 'admin' %}
                <li class="nav-item">
                    <a class="nav-link {% if 'clients' in request.url.path %}active{% endif %}" 
                       href="/clients">
                        <i class="bi bi-building"></i> Clients
                    </a>
                </li>
                {% endif %}
                
                <!-- Vendors (Admin Only) -->
                {% if user.role == 'admin' %}
                <li class="nav-item">
                    <a class="nav-link {% if 'vendors' in request.url.path %}active{% endif %}" 
                       href="/vendors">
                        <i class="bi bi-box-seam"></i> Vendors
                    </a>
                </li>
                {% endif %}
                
                <!-- Users (Admin Only) -->
                {% if user.role == 'admin' %}
                <li class="nav-item">
                    <a class="nav-link {% if 'users' in request.url.path %}active{% endif %}" 
                       href="/users">
                        <i class="bi bi-person-gear"></i> Users
                    </a>
                </li>
                {% endif %}
            </ul>
            
            <!-- User Menu -->
            <ul class="navbar-nav">
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" id="userDropdown" 
                       role="button" data-bs-toggle="dropdown">
                        <i class="bi bi-person-circle"></i>
                        {{ user.name }}
                        <span class="badge bg-light text-dark ms-1" style="font-size: 0.7rem;">
                            {{ user.role|title }}
                        </span>
                    </a>
                    <ul class="dropdown-menu dropdown-menu-end">
                        <li>
                            <a class="dropdown-item" href="/profile">
                                <i class="bi bi-person"></i> Profile
                            </a>
                        </li>
                        <li>
                            <a class="dropdown-item" href="/settings">
                                <i class="bi bi-gear"></i> Settings
                            </a>
                        </li>
                        <li><hr class="dropdown-divider"></li>
                        <li>
                            <a class="dropdown-item" href="/logout">
                                <i class="bi bi-box-arrow-right"></i> Logout
                            </a>
                        </li>
                    </ul>
                </li>
            </ul>
        </div>
    </div>
</nav>

<style>
    .navbar .nav-link {
        border-radius: 0.375rem;
        margin: 0 0.25rem;
        padding: 0.5rem 1rem !important;
        transition: background-color 0.2s;
    }
    
    .navbar .nav-link:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    .navbar .nav-link.active {
        background-color: rgba(255, 255, 255, 0.2);
        font-weight: 600;
    }
</style>
```

### Button Styles

```html
<!-- Primary Button -->
<button class="btn btn-primary">
    <i class="bi bi-plus-circle"></i> Primary Action
</button>

<!-- Secondary Button -->
<button class="btn btn-outline-primary">
    Secondary Action
</button>

<!-- Success Button -->
<button class="btn btn-success">
    <i class="bi bi-check-circle"></i> Approve
</button>

<!-- Danger Button -->
<button class="btn btn-danger">
    <i class="bi bi-x-circle"></i> Reject
</button>

<!-- Icon Button -->
<button class="btn btn-sm btn-outline-secondary">
    <i class="bi bi-eye"></i>
</button>
```

### Card Styles

```html
<!-- Standard Card -->
<div class="card">
    <div class="card-header">
        <h5 class="mb-0">Card Title</h5>
    </div>
    <div class="card-body">
        Card content goes here
    </div>
</div>

<!-- Metric Card -->
<div class="card text-center">
    <div class="card-body">
        <div class="text-muted mb-2">Total Candidates</div>
        <h2 class="mb-0">1,234</h2>
        <small class="text-success">
            <i class="bi bi-arrow-up"></i> +15% this month
        </small>
    </div>
</div>
```

### Badge Styles

```html
<!-- Status Badges -->
<span class="badge bg-primary">New</span>
<span class="badge bg-warning text-dark">Shortlisted</span>
<span class="badge bg-info">Interviewed</span>
<span class="badge bg-success">Hired</span>
<span class="badge bg-danger">Rejected</span>

<!-- Score Badges -->
<span class="badge" style="background: #10B981;">92%</span>  <!-- High -->
<span class="badge" style="background: #F59E0B;">75%</span>  <!-- Medium -->
<span class="badge" style="background: #EF4444;">45%</span>  <!-- Low -->
```

---

## 📄 Template Structure

### Base Template

**File:** `templates/base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}AI Powered HR Assistant{% endblock %}</title>
    
    <!-- Bootstrap 5 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" 
          rel="stylesheet">
    
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" 
          href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="/static/css/unified_styles.css">
    
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Unified Navigation -->
    {% include 'components/unified_navbar.html' %}
    
    <!-- Main Content -->
    <main class="main-content">
        <div class="container-fluid px-4 py-4">
            {% block content %}{% endblock %}
        </div>
    </main>
    
    <!-- Footer -->
    <footer class="footer mt-auto py-3 bg-light">
        <div class="container text-center">
            <span class="text-muted">
                © 2025 AI Powered HR Assistant. All rights reserved.
            </span>
        </div>
    </footer>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Custom JS -->
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Page Template Structure

```html
{% extends "base.html" %}

{% block title %}Page Title - AI Powered HR Assistant{% endblock %}

{% block extra_css %}
<style>
    /* Page-specific styles */
</style>
{% endblock %}

{% block content %}
<!-- Page Header -->
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>
        <i class="bi bi-icon-name"></i>
        Page Title
    </h1>
    <div>
        <button class="btn btn-primary">Primary Action</button>
    </div>
</div>

<!-- Breadcrumb (optional) -->
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="/">Dashboard</a></li>
        <li class="breadcrumb-item active">Current Page</li>
    </ol>
</nav>

<!-- Page Content -->
<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-body">
                <!-- Content here -->
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
    // Page-specific JavaScript
</script>
{% endblock %}
```

---

## 📝 Implementation Checklist

### Phase 1: Create Components (Week 1)
- [ ] Create `templates/components/unified_navbar.html`
- [ ] Create `static/css/unified_styles.css`
- [ ] Update `templates/base.html` with unified structure
- [ ] Test navigation rendering
- [ ] Test role-based menu visibility

### Phase 2: Update Templates (Week 1-2)
- [ ] Update `templates/index.html`
- [ ] Update `templates/vet_resumes.html`
- [ ] Update `templates/upload.html`
- [ ] Update `templates/candidate_search.html`
- [ ] Update `templates/candidate_detail.html`
- [ ] Update `templates/resume_preview.html`
- [ ] Update `templates/jobs/job_list.html`
- [ ] Update `templates/jobs/job_detail.html`
- [ ] Update `templates/jobs/job_create.html`
- [ ] Update `templates/jobs_management/dashboard.html`
- [ ] Update `templates/users/user_list.html`
- [ ] Update all other templates (15+ files)

### Phase 3: Create Role Dashboards (Week 2)
- [ ] Create `templates/dashboards/hr_dashboard.html`
- [ ] Create `templates/dashboards/admin_dashboard.html`
- [ ] Create `templates/dashboards/vendor_dashboard.html`
- [ ] Implement dashboard routing in `main.py`
- [ ] Test dashboard access by role

### Phase 4: Testing (Week 2)
- [ ] Test responsive design (mobile, tablet, desktop)
- [ ] Test all navigation links
- [ ] Test role-based visibility
- [ ] Test all buttons and interactions
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Accessibility testing (screen readers, keyboard navigation)

---

## 🎨 CSS Guidelines

### Custom Styles File

**File:** `static/css/unified_styles.css`

```css
/* Global Styles */
:root {
    --primary-gradient-start: #667eea;
    --primary-gradient-end: #764ba2;
    --primary-solid: #4F46E5;
    /* ... other variables ... */
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--background);
    color: var(--text-primary);
}

/* Main Content */
.main-content {
    min-height: calc(100vh - 160px);
    padding-top: 76px; /* navbar height */
}

/* Cards */
.card {
    border: none;
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    transition: box-shadow 0.2s;
}

.card:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.card-header {
    background: white;
    border-bottom: 2px solid var(--background);
    font-weight: 600;
}

/* Buttons */
.btn-primary {
    background: linear-gradient(135deg, var(--primary-gradient-start) 0%, 
                                        var(--primary-gradient-end) 100%);
    border: none;
}

.btn-primary:hover {
    background: linear-gradient(135deg, var(--primary-hover) 0%, 
                                        var(--primary-gradient-end) 100%);
}

/* Status Badges */
.status-new { background: #3B82F6; }
.status-shortlisted { background: #F59E0B; }
.status-interviewed { background: #8B5CF6; }
.status-offered { background: #10B981; }
.status-hired { background: #059669; }
.status-rejected { background: #EF4444; }

/* Score Badges */
.score-high { background: #10B981; color: white; }
.score-medium { background: #F59E0B; color: #000; }
.score-low { background: #EF4444; color: white; }

/* Responsive Utilities */
@media (max-width: 768px) {
    .main-content {
        padding-top: 60px;
    }
}
```

---

## ✅ Success Criteria

- All pages use the unified navbar
- Consistent color scheme across the application
- Role-based menu visibility working correctly
- Responsive design on all devices
- Smooth transitions and hover effects
- Professional and modern appearance
- Consistent button and card styles
- Proper typography hierarchy

---

**Next Steps:**
1. Implement unified navbar component
2. Update all templates systematically
3. Test across devices and browsers
4. Gather user feedback
5. Iterate and refine
