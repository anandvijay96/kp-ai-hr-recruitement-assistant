# 🔧 Interview Scheduling & User Edit Implementation Guide

**Status:** Ready to implement  
**Files to modify:** 2 files  
**Estimated time:** 30 minutes

---

## 📋 **Changes Overview**

### **1. Interview Scheduling (candidate_detail.html)**
- Replace "coming soon" with actual modal
- Add date/time picker
- Connect to interview API
- Show success/error messages

### **2. User Edit (users/dashboard.html)**
- Replace "coming soon" with edit modal
- Add form for editing user details
- Add password change functionality
- Connect to user update API

---

## 🎯 **Implementation Steps**

### **Step 1: Interview Scheduling Modal**

**File:** `templates/candidate_detail.html`

**Location:** After line 1620 (where "coming soon" message is)

**Replace:**
```javascript
$('#scheduleInterviewBtn').click(() => {
    // Open interview scheduling modal
    showSuccessMessage('Interview scheduling feature coming soon!');
});
```

**With:**
```javascript
$('#scheduleInterviewBtn').click(() => {
    // Open interview scheduling modal
    $('#scheduleInterviewModal').modal('show');
    // Set candidate ID
    $('#interviewCandidateId').val(candidateId);
});
```

**Add Modal HTML** (before closing `</body>` tag):
```html
<!-- Interview Scheduling Modal -->
<div class="modal fade" id="scheduleInterviewModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="bi bi-calendar-check me-2"></i>Schedule Interview
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="scheduleInterviewForm">
                    <input type="hidden" id="interviewCandidateId">
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Interview Date & Time *</label>
                            <input type="datetime-local" class="form-control" id="interviewDateTime" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Duration (minutes) *</label>
                            <select class="form-select" id="interviewDuration" required>
                                <option value="30">30 minutes</option>
                                <option value="45">45 minutes</option>
                                <option value="60" selected>1 hour</option>
                                <option value="90">1.5 hours</option>
                                <option value="120">2 hours</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Interview Type *</label>
                            <select class="form-select" id="interviewType" required>
                                <option value="phone">Phone Screen</option>
                                <option value="video">Video Interview</option>
                                <option value="in_person">In-Person</option>
                                <option value="technical">Technical Round</option>
                                <option value="hr">HR Round</option>
                                <option value="final">Final Round</option>
                            </select>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Interview Round *</label>
                            <input type="number" class="form-control" id="interviewRound" value="1" min="1" required>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Location / Meeting Link</label>
                        <input type="text" class="form-control" id="interviewLocation" 
                               placeholder="Office address or video call link">
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Notes</label>
                        <textarea class="form-control" id="interviewNotes" rows="3" 
                                  placeholder="Additional notes for the interview"></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="submitInterview()">
                    <i class="bi bi-calendar-check me-1"></i>Schedule Interview
                </button>
            </div>
        </div>
    </div>
</div>
```

**Add JavaScript Function:**
```javascript
async function submitInterview() {
    const candidateId = $('#interviewCandidateId').val();
    const jobId = '{{ candidate.applied_jobs[0].id if candidate.applied_jobs else "" }}'; // Get from context
    
    const data = {
        candidate_id: candidateId,
        job_id: jobId || null,
        scheduled_datetime: new Date($('#interviewDateTime').val()).toISOString(),
        interview_type: $('#interviewType').val(),
        duration_minutes: parseInt($('#interviewDuration').val()),
        location: $('#interviewLocation').val() || null,
        meeting_link: $('#interviewLocation').val() || null,
        notes: $('#interviewNotes').val() || null,
        interview_round: parseInt($('#interviewRound').val())
    };
    
    try {
        const response = await fetch('/api/v1/interviews', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            $('#scheduleInterviewModal').modal('hide');
            showSuccessMessage('Interview scheduled successfully!');
            // Reset form
            $('#scheduleInterviewForm')[0].reset();
        } else {
            showErrorMessage(result.detail || 'Failed to schedule interview');
        }
    } catch (error) {
        console.error('Error scheduling interview:', error);
        showErrorMessage('Failed to schedule interview. Please try again.');
    }
}
```

---

### **Step 2: User Edit Modal**

**File:** `templates/users/dashboard.html`

**Location:** Replace line 622-625

**Replace:**
```javascript
function editUser(userId) {
    // TODO: Implement edit functionality
    showAlert('Edit functionality coming soon', 'info');
}
```

**With:**
```javascript
async function editUser(userId) {
    try {
        // Fetch user details
        const response = await fetch(`/api/users/${userId}`);
        const data = await response.json();
        
        if (response.ok) {
            // Populate form
            $('#editUserId').val(data.id);
            $('#editFullName').val(data.full_name);
            $('#editEmail').val(data.email);
            $('#editMobile').val(data.mobile);
            $('#editRole').val(data.role);
            $('#editDepartment').val(data.department || '');
            $('#editStatus').val(data.status);
            
            // Show modal
            $('#editUserModal').modal('show');
        } else {
            showAlert(data.detail || 'Failed to load user details', 'error');
        }
    } catch (error) {
        console.error('Error loading user:', error);
        showAlert('Failed to load user details', 'error');
    }
}
```

**Add Modal HTML** (before closing `</body>` tag):
```html
<!-- Edit User Modal -->
<div class="modal fade" id="editUserModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="bi bi-pencil-square me-2"></i>Edit User
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="editUserForm">
                    <input type="hidden" id="editUserId">
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Full Name *</label>
                            <input type="text" class="form-control" id="editFullName" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Email *</label>
                            <input type="email" class="form-control" id="editEmail" required>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Mobile *</label>
                            <input type="tel" class="form-control" id="editMobile" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Role *</label>
                            <select class="form-select" id="editRole" required>
                                <option value="admin">HR Admin</option>
                                <option value="manager">HR Manager</option>
                                <option value="recruiter">Recruiter</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Department</label>
                            <input type="text" class="form-control" id="editDepartment" 
                                   placeholder="e.g., Engineering, HR">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Status *</label>
                            <select class="form-select" id="editStatus" required>
                                <option value="active">Active</option>
                                <option value="inactive">Inactive</option>
                                <option value="locked">Locked</option>
                            </select>
                        </div>
                    </div>
                    
                    <hr class="my-4">
                    <h6 class="mb-3">Change Password (Optional)</h6>
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">New Password</label>
                            <input type="password" class="form-control" id="editNewPassword" 
                                   placeholder="Leave blank to keep current password">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Confirm Password</label>
                            <input type="password" class="form-control" id="editConfirmPassword">
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="submitUserEdit()">
                    <i class="bi bi-check-lg me-1"></i>Save Changes
                </button>
            </div>
        </div>
    </div>
</div>
```

**Add JavaScript Function:**
```javascript
async function submitUserEdit() {
    const userId = $('#editUserId').val();
    const newPassword = $('#editNewPassword').val();
    const confirmPassword = $('#editConfirmPassword').val();
    
    // Validate passwords if provided
    if (newPassword || confirmPassword) {
        if (newPassword !== confirmPassword) {
            showAlert('Passwords do not match', 'error');
            return;
        }
        if (newPassword.length < 8) {
            showAlert('Password must be at least 8 characters', 'error');
            return;
        }
    }
    
    const data = {
        full_name: $('#editFullName').val(),
        email: $('#editEmail').val(),
        mobile: $('#editMobile').val(),
        role: $('#editRole').val(),
        department: $('#editDepartment').val() || null,
        status: $('#editStatus').val()
    };
    
    // Add password if provided
    if (newPassword) {
        data.new_password = newPassword;
    }
    
    try {
        const response = await fetch(`/api/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            $('#editUserModal').modal('hide');
            showAlert('User updated successfully!', 'success');
            // Reload users list
            loadUsers();
        } else {
            showAlert(result.detail || 'Failed to update user', 'error');
        }
    } catch (error) {
        console.error('Error updating user:', error);
        showAlert('Failed to update user. Please try again.', 'error');
    }
}
```

---

## 🧪 **Testing Checklist**

### **Interview Scheduling:**
- [ ] Click "Schedule Interview" button
- [ ] Modal opens
- [ ] Fill in all fields
- [ ] Submit form
- [ ] Success message shows
- [ ] Interview appears in upcoming interviews

### **User Edit:**
- [ ] Click edit button on user
- [ ] Modal opens with user data
- [ ] Edit user details
- [ ] Submit without password change
- [ ] Success message shows
- [ ] User list refreshes
- [ ] Edit again with password change
- [ ] Verify password updated

---

## 📝 **Notes**

### **Interview Scheduling:**
- Uses existing `/api/v1/interviews` endpoint
- Supports all interview types
- Includes conflict detection
- Can add multiple interviewers (future enhancement)

### **User Edit:**
- Uses existing `/api/users/{id}` endpoint
- Supports password changes
- Validates password match
- Refreshes user list after update

---

**Ready to implement!** 🚀

These changes will make the application production-ready for user management and interview scheduling.
