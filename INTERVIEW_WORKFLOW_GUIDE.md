# 📅 Interview Scheduling Workflow Guide

**Complete guide to interview scheduling and management**

---

## 🎯 **What Happens After Scheduling an Interview?**

### **1. Interview is Created in Database** ✅

When you schedule an interview, it's stored in the `interviews` table with:
- Candidate ID
- Job ID (optional)
- Scheduled date/time
- Interview type (phone, video, in-person, technical, HR, final)
- Duration
- Location/meeting link
- Notes
- Status: `scheduled`
- Interview round number

---

## 📊 **Where Can HR/Admin Check Interview Status?**

### **Current Implementation (Phase 3):**

#### **Option 1: API Endpoints** ✅

**Get Upcoming Interviews:**
```bash
GET /api/v1/interviews/upcoming?days_ahead=7
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "abc123",
      "candidate_id": "76aff8e0-48cd-42e9-8aab-d2c26c5d4d9d",
      "job_id": "job-001",
      "scheduled_datetime": "2025-10-20T14:00:00",
      "interview_type": "phone",
      "duration_minutes": 60,
      "status": "scheduled",
      "location": "Office Room 301",
      "meeting_link": "https://meet.google.com/abc-defg-hij"
    }
  ]
}
```

**Get Candidate's Interviews:**
```bash
GET /api/v1/candidates/{candidate_id}/interviews
```

---

### **Option 2: UI Pages (TO BE IMPLEMENTED)** 🔄

#### **A. Interview Dashboard Page** (Recommended)
**URL:** `/interviews` or `/interviews/dashboard`

**Features Needed:**
- Calendar view of all scheduled interviews
- List view with filters (today, this week, upcoming)
- Status indicators (scheduled, completed, cancelled)
- Quick actions (reschedule, cancel, mark complete)
- Interviewer assignments
- Conflict detection

**Layout:**
```
┌─────────────────────────────────────────────┐
│  📅 Interview Dashboard                     │
├─────────────────────────────────────────────┤
│  Filters: [Today] [This Week] [All]        │
│  Status: [Scheduled] [Completed] [Cancelled]│
├─────────────────────────────────────────────┤
│  📆 Oct 20, 2025 - 2:00 PM                  │
│  👤 LAHARI BAYYAKKAGARI                     │
│  💼 Data Scientist Position                 │
│  📞 Phone Screen (Round 1)                  │
│  ⏱️ Duration: 1 hour                        │
│  📍 https://meet.google.com/abc             │
│  [Reschedule] [Cancel] [Mark Complete]     │
├─────────────────────────────────────────────┤
│  📆 Oct 21, 2025 - 10:00 AM                 │
│  👤 Ranga Reddy Mandalapu                   │
│  💼 Senior Engineer Position                │
│  💻 Technical Round (Round 2)               │
│  ⏱️ Duration: 2 hours                       │
│  📍 Office - Room 301                       │
│  [Reschedule] [Cancel] [Mark Complete]     │
└─────────────────────────────────────────────┘
```

---

#### **B. Candidate Detail Page Enhancement** (Partially Done)
**URL:** `/candidates/{id}`

**Add Interview Section:**
```
┌─────────────────────────────────────────────┐
│  📅 Scheduled Interviews                    │
├─────────────────────────────────────────────┤
│  ✅ Round 1 - Phone Screen                  │
│     Oct 15, 2025 - Completed               │
│     Interviewer: John Doe                   │
│     Rating: 4/5                             │
│                                             │
│  📆 Round 2 - Technical Interview           │
│     Oct 20, 2025 - 2:00 PM (Upcoming)      │
│     Duration: 2 hours                       │
│     Location: Office Room 301               │
│     [Reschedule] [Cancel]                   │
│                                             │
│  [+ Schedule Next Round]                    │
└─────────────────────────────────────────────┘
```

---

#### **C. Calendar View** (Future Enhancement)
**URL:** `/interviews/calendar`

**Features:**
- Full calendar with interview slots
- Drag-and-drop rescheduling
- Color-coded by interview type
- Interviewer availability
- Conflict warnings

---

## 🔄 **Interview Lifecycle**

### **Status Flow:**

```
scheduled → in_progress → completed
    ↓
cancelled
    ↓
rescheduled → scheduled
```

### **1. Scheduled** 📅
- Interview is created
- Candidate and interviewer notified (email - future)
- Shows in upcoming interviews
- Can be rescheduled or cancelled

### **2. In Progress** ⏳
- Interview is currently happening
- Status can be manually updated
- Timer shows elapsed time

### **3. Completed** ✅
- Interview finished
- Feedback can be added
- Rating recorded
- Recommendation noted
- Next round can be scheduled

### **4. Cancelled** ❌
- Interview cancelled
- Reason recorded
- Can be rescheduled

### **5. Rescheduled** 🔄
- Original interview cancelled
- New interview created
- Linked to original

---

## 📝 **Interview Feedback & Rating**

### **After Interview Completion:**

**Endpoint:** `POST /api/v1/interviews/{id}/complete`

**Payload:**
```json
{
  "rating": 4,
  "feedback": "Strong technical skills, good communication",
  "recommendation": "proceed",
  "notes": "Candidate showed excellent problem-solving abilities"
}
```

**Recommendations:**
- `proceed` - Move to next round
- `hire` - Make offer
- `reject` - Don't proceed
- `maybe` - Need more evaluation

---

## 🔔 **Notifications (Future Enhancement)**

### **Email Notifications:**
- Interview scheduled → Candidate + Interviewer
- Interview reminder → 24 hours before
- Interview reminder → 1 hour before
- Interview rescheduled → All parties
- Interview cancelled → All parties
- Feedback requested → Interviewer

### **In-App Notifications:**
- Dashboard badge with upcoming count
- Toast notifications for reminders
- Calendar integration

---

## 🎯 **Next Steps to Complete Interview Management**

### **Priority 1: Interview Dashboard Page** 🔥

**Create:** `templates/interviews/dashboard.html`

**Features:**
1. List all upcoming interviews
2. Filter by date range
3. Filter by status
4. Quick actions (reschedule, cancel, complete)
5. Search by candidate name
6. Sort by date/time

**Implementation:**
```python
# main.py
@app.get("/interviews")
@require_auth
async def interviews_dashboard(request: Request):
    """Interview dashboard page"""
    user = await get_current_user(request)
    return templates.TemplateResponse("interviews/dashboard.html", {
        "request": request,
        "user": user
    })
```

---

### **Priority 2: Add Interview Section to Candidate Detail** 🔥

**Update:** `templates/candidate_detail.html`

**Add:**
1. "Scheduled Interviews" section
2. Load interviews via API
3. Display interview history
4. Show upcoming interviews
5. Quick reschedule/cancel buttons

**API Call:**
```javascript
async function loadCandidateInterviews() {
    const response = await fetch(`/api/v1/candidates/${candidateId}/interviews`);
    const data = await response.json();
    displayInterviews(data.interviews);
}
```

---

### **Priority 3: Interview Actions** 🔥

**Endpoints Already Exist:**
- ✅ Schedule interview
- ✅ Get upcoming interviews
- ✅ Get candidate interviews
- ⏳ Reschedule interview (exists in API)
- ⏳ Cancel interview (exists in API)
- ⏳ Complete interview (exists in API)

**Need UI for:**
- Reschedule modal
- Cancel confirmation
- Complete interview form (feedback + rating)

---

### **Priority 4: Email Notifications** 📧

**Options:**
1. **SendGrid** (recommended)
2. **AWS SES**
3. **Mailgun**
4. **SMTP** (Gmail, Outlook)

**Implementation:**
```python
# services/email_service.py
async def send_interview_scheduled_email(
    candidate_email: str,
    candidate_name: str,
    interview_datetime: datetime,
    interview_type: str,
    meeting_link: str
):
    # Send email via SendGrid
    pass
```

---

## 📋 **Quick Implementation Checklist**

### **Phase 1: Basic Dashboard** (2-3 hours)
- [ ] Create `/interviews` route
- [ ] Create `templates/interviews/dashboard.html`
- [ ] Load upcoming interviews via API
- [ ] Display in table/card format
- [ ] Add basic filters (today, this week, all)

### **Phase 2: Candidate Detail Integration** (1-2 hours)
- [ ] Add "Interviews" section to candidate detail
- [ ] Load candidate's interviews
- [ ] Display interview history
- [ ] Show upcoming interviews
- [ ] Add "Schedule Next Round" button

### **Phase 3: Interview Actions** (2-3 hours)
- [ ] Add reschedule modal
- [ ] Add cancel confirmation
- [ ] Add complete interview form
- [ ] Implement API calls
- [ ] Update UI after actions

### **Phase 4: Email Notifications** (3-4 hours)
- [ ] Set up SendGrid account
- [ ] Create email templates
- [ ] Implement email service
- [ ] Send on schedule/reschedule/cancel
- [ ] Add email preferences

---

## 🎨 **UI Mockup: Interview Dashboard**

```html
<!-- templates/interviews/dashboard.html -->
<div class="container-fluid mt-4">
    <div class="row mb-4">
        <div class="col-md-12">
            <h2><i class="bi bi-calendar-check me-2"></i>Interview Dashboard</h2>
        </div>
    </div>
    
    <!-- Summary Cards -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5>Today</h5>
                    <h2 class="text-primary">3</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5>This Week</h5>
                    <h2 class="text-info">12</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5>Completed</h5>
                    <h2 class="text-success">45</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5>Cancelled</h5>
                    <h2 class="text-danger">5</h2>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Filters -->
    <div class="row mb-3">
        <div class="col-md-12">
            <button class="btn btn-primary">Today</button>
            <button class="btn btn-outline-primary">This Week</button>
            <button class="btn btn-outline-primary">All Upcoming</button>
            <button class="btn btn-outline-secondary">Completed</button>
        </div>
    </div>
    
    <!-- Interview List -->
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-body">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Date & Time</th>
                                <th>Candidate</th>
                                <th>Job</th>
                                <th>Type</th>
                                <th>Round</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="interviewsTable">
                            <!-- Loaded via JavaScript -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

## 🚀 **Summary**

### **Currently Working:**
- ✅ Schedule interview from candidate detail page
- ✅ Store interview in database
- ✅ API endpoints for retrieving interviews

### **Missing (High Priority):**
- ❌ Interview dashboard page
- ❌ View scheduled interviews in UI
- ❌ Interview section in candidate detail
- ❌ Reschedule/cancel UI
- ❌ Complete interview form
- ❌ Email notifications

### **Recommended Next Steps:**
1. **Create interview dashboard** (`/interviews`)
2. **Add interview section to candidate detail**
3. **Implement reschedule/cancel/complete actions**
4. **Set up email notifications**

---

**The interview scheduling backend is complete. Now we need the UI to view and manage interviews!** 📅✨
