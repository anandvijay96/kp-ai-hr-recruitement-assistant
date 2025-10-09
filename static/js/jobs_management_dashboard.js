// Jobs Management Dashboard JavaScript

let currentPage = 1;
let currentFilters = {};
let selectedJobs = new Set();
let currentSort = { by: 'created_at', order: 'desc' };
let searchTimeout = null;
let currentJobId = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    loadDepartments();
});

// Load dashboard data
async function loadDashboard() {
    try {
        // Check authentication
        const token = getAuthToken();
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        const params = new URLSearchParams({
            page: currentPage,
            limit: 20,
            sort_by: currentSort.by,
            sort_order: currentSort.order,
            ...currentFilters
        });
        
        const response = await fetch(`/api/jobs-management/dashboard?${params}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        // Handle authentication errors
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            sessionStorage.removeItem('access_token');
            alert('Your session has expired. Please login again.');
            window.location.href = '/login';
            return;
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to load dashboard');
        }
        
        const data = await response.json();
        
        if (data.success) {
            updateSummaryCards(data.summary);
            renderJobsTable(data.jobs);
            renderPagination(data.pagination);
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
        const tbody = document.getElementById('jobs-table-body');
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center" style="padding: 40px;">
                    <div style="color: #dc3545;">
                        <h4>⚠️ Failed to load dashboard data</h4>
                        <p style="margin: 10px 0; color: #666;">${error.message}</p>
                        <button class="btn btn-primary" onclick="loadDashboard()">Retry</button>
                    </div>
                </td>
            </tr>
        `;
        showToast('Failed to load dashboard data: ' + error.message, 'error');
    }
}

// Update summary cards
function updateSummaryCards(summary) {
    document.getElementById('total-jobs').textContent = summary.total_jobs || 0;
    document.getElementById('open-jobs').textContent = summary.open || 0;
    document.getElementById('closed-jobs').textContent = summary.closed || 0;
    document.getElementById('onhold-jobs').textContent = summary.on_hold || 0;
    document.getElementById('archived-jobs').textContent = summary.archived || 0;
}

// Render jobs table
function renderJobsTable(jobs) {
    const tbody = document.getElementById('jobs-table-body');
    
    if (jobs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center">No jobs found</td></tr>';
        return;
    }
    
    tbody.innerHTML = jobs.map(job => `
        <tr>
            <td>
                <input type="checkbox" 
                       class="job-checkbox" 
                       data-job-id="${job.id}" 
                       onchange="toggleJobSelection('${job.id}')"
                       ${selectedJobs.has(job.id) ? 'checked' : ''}>
            </td>
            <td>
                <a href="/jobs/${job.id}" class="job-title">${escapeHtml(job.title)}</a>
            </td>
            <td>${escapeHtml(job.department || '--')}</td>
            <td><span class="status-badge status-${job.status}">${formatStatus(job.status)}</span></td>
            <td>${formatDate(job.posted_date)}</td>
            <td>${job.application_count}</td>
            <td>${job.avg_match_score ? job.avg_match_score.toFixed(1) + '%' : '--'}</td>
            <td>${job.view_count || 0}</td>
            <td class="actions-cell">
                <button class="btn-icon" onclick="viewAnalytics('${job.id}')" title="View Analytics">
                    <i class="icon-chart"></i>
                </button>
                <button class="btn-icon" onclick="changeStatus('${job.id}')" title="Change Status">
                    <i class="icon-edit"></i>
                </button>
                <button class="btn-icon" onclick="viewAuditLog('${job.id}')" title="Audit Log">
                    <i class="icon-history"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Render pagination
function renderPagination(pagination) {
    const container = document.getElementById('pagination');
    
    if (pagination.total_pages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    if (pagination.page > 1) {
        html += `<button onclick="goToPage(${pagination.page - 1})">Previous</button>`;
    }
    
    // Page numbers
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.total_pages, pagination.page + 2);
    
    if (startPage > 1) {
        html += `<button onclick="goToPage(1)">1</button>`;
        if (startPage > 2) html += '<span>...</span>';
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="${i === pagination.page ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }
    
    if (endPage < pagination.total_pages) {
        if (endPage < pagination.total_pages - 1) html += '<span>...</span>';
        html += `<button onclick="goToPage(${pagination.total_pages})">${pagination.total_pages}</button>`;
    }
    
    // Next button
    if (pagination.page < pagination.total_pages) {
        html += `<button onclick="goToPage(${pagination.page + 1})">Next</button>`;
    }
    
    container.innerHTML = html;
}

// Apply filters
function applyFilters() {
    currentFilters = {};
    
    const status = document.getElementById('filter-status').value;
    if (status) currentFilters.status = status;
    
    const department = document.getElementById('filter-department').value;
    if (department) currentFilters.department = department;
    
    const dateFrom = document.getElementById('filter-date-from').value;
    if (dateFrom) currentFilters.date_from = dateFrom;
    
    const dateTo = document.getElementById('filter-date-to').value;
    if (dateTo) currentFilters.date_to = dateTo;
    
    const search = document.getElementById('filter-search').value;
    if (search) currentFilters.search = search;
    
    currentPage = 1;
    loadDashboard();
}

// Debounced search
function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        applyFilters();
    }, 500);
}

// Sort by column
function sortBy(column) {
    if (currentSort.by === column) {
        currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.by = column;
        currentSort.order = 'desc';
    }
    loadDashboard();
}

// Go to page
function goToPage(page) {
    currentPage = page;
    loadDashboard();
}

// Change job status
function changeStatus(jobId) {
    currentJobId = jobId;
    document.getElementById('status-modal').style.display = 'flex';
    document.getElementById('status-form').reset();
}

// Submit status change
async function submitStatusChange(event) {
    event.preventDefault();
    
    const newStatus = document.getElementById('new-status').value;
    const reason = document.getElementById('status-reason').value;
    
    try {
        const response = await fetch(`/api/jobs-management/${currentJobId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({ status: newStatus, reason })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showToast('Job status updated successfully', 'success');
            closeModal('status-modal');
            loadDashboard();
        } else {
            showToast(data.detail || 'Failed to update status', 'error');
        }
    } catch (error) {
        console.error('Error updating status:', error);
        showToast('Failed to update job status', 'error');
    }
}

// Toggle job selection
function toggleJobSelection(jobId) {
    if (selectedJobs.has(jobId)) {
        selectedJobs.delete(jobId);
    } else {
        selectedJobs.add(jobId);
    }
    updateBulkActionsToolbar();
}

// Toggle select all
function toggleSelectAll() {
    const selectAll = document.getElementById('select-all').checked;
    const checkboxes = document.querySelectorAll('.job-checkbox');
    
    checkboxes.forEach(checkbox => {
        const jobId = checkbox.dataset.jobId;
        checkbox.checked = selectAll;
        if (selectAll) {
            selectedJobs.add(jobId);
        } else {
            selectedJobs.delete(jobId);
        }
    });
    
    updateBulkActionsToolbar();
}

// Update bulk actions toolbar
function updateBulkActionsToolbar() {
    const toolbar = document.getElementById('bulk-actions');
    const count = selectedJobs.size;
    
    if (count > 0) {
        toolbar.style.display = 'flex';
        document.getElementById('selected-count').textContent = `${count} job${count > 1 ? 's' : ''} selected`;
    } else {
        toolbar.style.display = 'none';
    }
}

// Clear selection
function clearSelection() {
    selectedJobs.clear();
    document.querySelectorAll('.job-checkbox').forEach(cb => cb.checked = false);
    document.getElementById('select-all').checked = false;
    updateBulkActionsToolbar();
}

// Bulk update status
function bulkUpdateStatus() {
    if (selectedJobs.size === 0) {
        showToast('Please select jobs first', 'warning');
        return;
    }
    
    document.getElementById('bulk-count').textContent = selectedJobs.size;
    document.getElementById('bulk-modal').style.display = 'flex';
    document.getElementById('bulk-form').reset();
}

// Submit bulk update
async function submitBulkUpdate(event) {
    event.preventDefault();
    
    const newStatus = document.getElementById('bulk-status').value;
    const reason = document.getElementById('bulk-reason').value;
    
    try {
        const response = await fetch('/api/jobs-management/bulk-update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                job_ids: Array.from(selectedJobs),
                operation: 'status_update',
                parameters: { status: newStatus, reason }
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(`Bulk operation initiated for ${selectedJobs.size} jobs`, 'success');
            closeModal('bulk-modal');
            clearSelection();
            loadDashboard();
        } else {
            showToast(data.detail || 'Failed to initiate bulk operation', 'error');
        }
    } catch (error) {
        console.error('Error in bulk update:', error);
        showToast('Failed to perform bulk update', 'error');
    }
}

// Bulk archive
async function bulkArchive() {
    if (selectedJobs.size === 0) {
        showToast('Please select jobs first', 'warning');
        return;
    }
    
    if (!confirm(`Are you sure you want to archive ${selectedJobs.size} job(s)?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/jobs-management/bulk-update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                job_ids: Array.from(selectedJobs),
                operation: 'archive',
                parameters: {}
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(`Bulk archive initiated for ${selectedJobs.size} jobs`, 'success');
            clearSelection();
            loadDashboard();
        } else {
            showToast(data.detail || 'Failed to archive jobs', 'error');
        }
    } catch (error) {
        console.error('Error in bulk archive:', error);
        showToast('Failed to archive jobs', 'error');
    }
}

// View analytics
function viewAnalytics(jobId) {
    window.location.href = `/jobs-management/${jobId}/analytics`;
}

// View audit log
function viewAuditLog(jobId) {
    window.location.href = `/jobs-management/${jobId}/audit-log`;
}

// Export jobs
async function exportJobs() {
    try {
        const params = new URLSearchParams(currentFilters);
        const response = await fetch(`/api/jobs-management/export?${params}`, {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `jobs_export_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            showToast('Jobs exported successfully', 'success');
        } else {
            showToast('Failed to export jobs', 'error');
        }
    } catch (error) {
        console.error('Error exporting jobs:', error);
        showToast('Failed to export jobs', 'error');
    }
}

// Load departments for filter
async function loadDepartments() {
    try {
        const response = await fetch('/api/jobs/departments', {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const select = document.getElementById('filter-department');
            data.departments?.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept;
                option.textContent = dept;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading departments:', error);
    }
}

// Utility functions
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast toast-${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function formatDate(dateString) {
    if (!dateString) return '--';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatStatus(status) {
    return status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getAuthToken() {
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || '';
}
