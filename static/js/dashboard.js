/**
 * Dashboard JavaScript
 * Handles data loading and rendering for dashboard widgets
 */

// Load dashboard data on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboardData();
    
    // Refresh every 5 minutes
    setInterval(loadDashboardData, 300000);
});

/**
 * Main function to load all dashboard data
 */
async function loadDashboardData() {
    try {
        const response = await fetch('/api/v1/dashboard/hr');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Render all dashboard sections
        renderQuickStats(data.stats);
        renderPendingVetting(data.pending_vetting || []);
        renderRecentCandidates(data.recent_candidates || []);
        renderActiveJobs(data.active_jobs || []);
        renderRecentActivity(data.recent_activity || []);
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load dashboard data. Please refresh the page.');
    }
}

/**
 * Render quick stats cards
 */
function renderQuickStats(stats) {
    const container = document.getElementById('quickStats');
    
    if (!stats) {
        container.innerHTML = '<div class="col-12"><p class="text-center text-muted">No stats available</p></div>';
        return;
    }
    
    container.innerHTML = `
        <div class="col-md-3 col-sm-6 mb-3">
            <div class="card stat-card h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-muted mb-2 text-uppercase" style="font-size: 0.75rem; font-weight: 600;">
                                Total Candidates
                            </h6>
                            <h2 class="mb-0 fw-bold">${stats.total_candidates || 0}</h2>
                        </div>
                        <div class="stat-icon">
                            <i class="bi bi-people-fill"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3 col-sm-6 mb-3">
            <div class="card stat-card h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-muted mb-2 text-uppercase" style="font-size: 0.75rem; font-weight: 600;">
                                Pending Vetting
                            </h6>
                            <h2 class="mb-0 fw-bold">${stats.pending_vetting || 0}</h2>
                            ${stats.pending_vetting > 0 ? '<span class="badge bg-warning text-dark mt-2">Action Required</span>' : ''}
                        </div>
                        <div class="stat-icon">
                            <i class="bi bi-shield-check"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3 col-sm-6 mb-3">
            <div class="card stat-card h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-muted mb-2 text-uppercase" style="font-size: 0.75rem; font-weight: 600;">
                                Shortlisted
                            </h6>
                            <h2 class="mb-0 fw-bold">${stats.shortlisted || 0}</h2>
                        </div>
                        <div class="stat-icon">
                            <i class="bi bi-star-fill"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3 col-sm-6 mb-3">
            <div class="card stat-card h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-muted mb-2 text-uppercase" style="font-size: 0.75rem; font-weight: 600;">
                                Active Jobs
                            </h6>
                            <h2 class="mb-0 fw-bold">${stats.active_jobs || 0}</h2>
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

/**
 * Render pending vetting list
 */
function renderPendingVetting(items) {
    const container = document.getElementById('pendingVetting');
    const countBadge = document.getElementById('pendingCount');
    
    countBadge.textContent = items.length;
    
    if (items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-check-circle-fill"></i>
                <p>All caught up! No pending resumes to vet.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = items.slice(0, 5).map(item => `
        <div class="list-item">
            <div class="d-flex justify-content-between align-items-center">
                <div class="flex-grow-1">
                    <h6 class="mb-1">${escapeHtml(item.name || 'Unknown Candidate')}</h6>
                    <small class="text-muted">
                        <i class="bi bi-clock"></i> ${formatTimeAgo(item.uploaded_at)}
                        ${item.position ? `<span class="mx-2">•</span><i class="bi bi-briefcase"></i> ${escapeHtml(item.position)}` : ''}
                    </small>
                </div>
                <a href="/vet-resumes?resume=${item.id}" class="btn btn-sm btn-primary ms-3">
                    Review
                </a>
            </div>
        </div>
    `).join('');
}

/**
 * Render recent candidates list
 */
function renderRecentCandidates(items) {
    const container = document.getElementById('recentCandidates');
    
    if (items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-inbox"></i>
                <p>No recent candidates</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = items.slice(0, 5).map(item => `
        <div class="candidate-card" onclick="window.location.href='/candidates/${item.id}'">
            <div class="candidate-header">
                <h6>${escapeHtml(item.name || 'Unknown')}</h6>
                ${item.score ? `<span class="score-badge ${getScoreClass(item.score)}">${item.score}%</span>` : ''}
            </div>
            <div class="candidate-meta">
                ${item.status ? `
                    <span class="candidate-meta-item">
                        <i class="bi bi-circle-fill" style="font-size: 0.5rem; color: ${getStatusColor(item.status)}"></i>
                        ${escapeHtml(item.status)}
                    </span>
                ` : ''}
                ${item.position ? `
                    <span class="candidate-meta-item">
                        <i class="bi bi-briefcase"></i>
                        ${escapeHtml(item.position)}
                    </span>
                ` : ''}
                <span class="candidate-meta-item">
                    <i class="bi bi-clock"></i>
                    ${formatTimeAgo(item.created_at)}
                </span>
            </div>
        </div>
    `).join('');
}

/**
 * Render active jobs list
 */
function renderActiveJobs(items) {
    const container = document.getElementById('activeJobs');
    
    if (items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-briefcase"></i>
                <p>No active jobs</p>
                <a href="/jobs/create" class="btn btn-sm btn-primary mt-2">Create Job</a>
            </div>
        `;
        return;
    }
    
    container.innerHTML = items.slice(0, 5).map(item => `
        <div class="job-card" onclick="window.location.href='/jobs/${item.id}'">
            <h6>${escapeHtml(item.title || 'Untitled Job')}</h6>
            <div class="job-meta">
                <span class="job-meta-item">
                    <i class="bi bi-people"></i>
                    ${item.candidate_count || 0} candidates
                </span>
                <span class="job-meta-item">
                    <i class="bi bi-calendar"></i>
                    Open ${item.days_open || 0} days
                </span>
                ${item.department ? `
                    <span class="job-meta-item">
                        <i class="bi bi-building"></i>
                        ${escapeHtml(item.department)}
                    </span>
                ` : ''}
            </div>
            <div class="d-flex gap-2">
                <span class="badge bg-primary">${escapeHtml(item.status || 'Active')}</span>
                ${item.priority ? `<span class="badge bg-warning text-dark">${escapeHtml(item.priority)}</span>` : ''}
            </div>
        </div>
    `).join('');
}

/**
 * Render recent activity feed
 */
function renderRecentActivity(items) {
    const container = document.getElementById('recentActivity');
    
    if (items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-clock-history"></i>
                <p>No recent activity</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = items.slice(0, 10).map(item => `
        <div class="activity-item">
            <div class="activity-icon icon-${item.type || 'upload'}">
                <i class="bi bi-${getActivityIcon(item.type)}"></i>
            </div>
            <div class="activity-content">
                <p>${escapeHtml(item.description || 'Activity')}</p>
                <small>${formatTimeAgo(item.timestamp)}</small>
            </div>
        </div>
    `).join('');
}

/**
 * Utility Functions
 */

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTimeAgo(timestamp) {
    if (!timestamp) return 'Unknown';
    
    const now = new Date();
    const date = new Date(timestamp);
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;
    
    return date.toLocaleDateString();
}

function getScoreClass(score) {
    if (score >= 80) return 'score-high bg-success text-white';
    if (score >= 60) return 'score-medium bg-warning text-dark';
    return 'score-low bg-danger text-white';
}

function getStatusColor(status) {
    const colors = {
        'new': '#3B82F6',
        'shortlisted': '#F59E0B',
        'interviewed': '#8B5CF6',
        'offered': '#10B981',
        'hired': '#059669',
        'rejected': '#EF4444'
    };
    return colors[status.toLowerCase()] || '#6B7280';
}

function getActivityIcon(type) {
    const icons = {
        'upload': 'cloud-upload',
        'vet': 'shield-check',
        'shortlist': 'star',
        'interview': 'calendar-check',
        'hired': 'check-circle',
        'rejected': 'x-circle'
    };
    return icons[type] || 'circle';
}

function showError(message) {
    // You can implement a toast notification here
    console.error(message);
}
