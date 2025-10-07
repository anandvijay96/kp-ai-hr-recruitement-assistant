# PRD: Candidate Tracking System

**Feature ID:** 04  
**Feature Name:** Candidate Tracking System  
**Priority:** P0 (Critical)  
**Complexity:** High  
**Estimated Effort:** 4-5 weeks  
**Phase:** 2 (Tracking & Collaboration)  
**Dependencies:** Features 2, 3

---

## 1. Overview

### 1.1 Description
Comprehensive candidate lifecycle tracking system with visual pipeline, interview scheduling, calendar integration, automated notifications, and team collaboration features.

### 1.2 Business Value
- **Efficiency:** Reduce interview scheduling time by 70%
- **Transparency:** 100% visibility into candidate status
- **Collaboration:** Enable team coordination on candidates
- **Automation:** Reduce manual communication by 60%

### 1.3 Success Metrics
- 100% accurate status tracking
- Calendar integration working for Google & Outlook
- Email delivery rate > 98%
- Interview scheduling time < 5 minutes per candidate
- Real-time notifications < 5 second delay

---

## 2. User Stories

### US-4.1: Status Pipeline Management
```
As a recruiter
I want to track candidate progress through stages
So that I know where each candidate is in the hiring process

Acceptance Criteria:
- [ ] Visual kanban board interface
- [ ] Drag-and-drop status changes
- [ ] Status: Received → Shortlisted → Interviewed → Offered → Hired/Rejected
- [ ] Automatic timestamp for each status change
- [ ] History log of all status changes
- [ ] Bulk status updates
```

### US-4.2: Interview Scheduling
```
As a recruiter
I want to schedule interviews with calendar integration
So that I can coordinate with interviewers and candidates efficiently

Acceptance Criteria:
- [ ] Calendar integration (Google, Outlook)
- [ ] Check interviewer availability
- [ ] Send interview invites automatically
- [ ] Include video call links (Zoom, Teams, Meet)
- [ ] Send reminders 24 hours before
- [ ] Track interview confirmations
- [ ] Support multiple interview rounds
```

### US-4.3: Candidate Response Tracking
```
As a recruiter
I want to track candidate responses
So that I know who has confirmed, declined, or not responded

Acceptance Criteria:
- [ ] Track email open rate
- [ ] Track interview confirmations
- [ ] Track offer acceptances/rejections
- [ ] Flag non-responsive candidates
- [ ] Automatic follow-up reminders
- [ ] Response status dashboard
```

### US-4.4: Timeline View
```
As a recruiter
I want to see a timeline of all candidate interactions
So that I have complete context for decision making

Acceptance Criteria:
- [ ] Chronological activity feed
- [ ] Show: status changes, interviews, emails, comments
- [ ] Filter by activity type
- [ ] Export timeline as PDF
- [ ] Search within timeline
```

### US-4.5: Notifications & Reminders
```
As a recruiter
I want to receive notifications for pending actions
So that I don't miss important follow-ups

Acceptance Criteria:
- [ ] Real-time browser notifications
- [ ] Email digest (daily/weekly)
- [ ] Notification types: interview scheduled, response received, status change
- [ ] Configurable notification preferences
- [ ] Mark notifications as read
- [ ] Snooze notifications
```

### US-4.6: Team Collaboration
```
As a recruiter
I want to add comments and feedback on candidates
So that my team can collaborate on hiring decisions

Acceptance Criteria:
- [ ] Add comments on candidate profile
- [ ] @mention team members
- [ ] Attach files to comments
- [ ] Edit/delete own comments
- [ ] Comment notifications
- [ ] Comment history
```

---

## 3. Functional Requirements

### 3.1 Status Pipeline

**FR-4.1.1: Status Stages**
```
1. Received (Initial state after resume upload)
2. Shortlisted (Marked as potential fit)
3. Phone Screen Scheduled
4. Phone Screen Completed
5. Technical Interview Scheduled
6. Technical Interview Completed
7. Final Interview Scheduled
8. Final Interview Completed
9. Offer Extended
10. Offer Accepted → Hired
11. Offer Declined → Rejected
12. Rejected (Any stage)
```

**FR-4.1.2: Status Transitions**
- Allow forward and backward transitions
- Require reason for moving to "Rejected"
- Auto-archive after 90 days in "Hired" or "Rejected"
- Bulk status updates (max 50 candidates)

**FR-4.1.3: Status Metadata**
- Timestamp of change
- Changed by (user)
- Reason/notes
- Previous status
- Days in current status

### 3.2 Interview Scheduling

**FR-4.2.1: Calendar Integration**

**Google Calendar:**
```python
# OAuth2 authentication
# Create calendar event
# Add attendees
# Send invitations
# Handle responses
```

**Microsoft Outlook:**
```python
# Microsoft Graph API
# Create event
# Add attendees
# Send invitations
```

**FR-4.2.2: Interview Types**
- Phone Screen (30 min)
- Technical Interview (60-90 min)
- Cultural Fit Interview (45 min)
- Final/Panel Interview (60-120 min)
- Custom types

**FR-4.2.3: Interview Details**
```json
{
    "type": "technical_interview",
    "date": "2025-10-15",
    "time": "14:00",
    "duration_minutes": 90,
    "location": "Conference Room A / Zoom Link",
    "interviewers": [
        {"name": "John Manager", "email": "john@company.com"}
    ],
    "candidate_id": 123,
    "job_id": 456,
    "meeting_link": "https://zoom.us/j/123456",
    "notes": "Focus on system design",
    "status": "scheduled"  // scheduled, completed, cancelled, no_show
}
```

**FR-4.2.4: Email Templates**
- Interview invitation
- Interview confirmation
- Interview reminder (24h before)
- Interview reschedule
- Interview cancellation
- Interview feedback request

### 3.3 Response Tracking

**FR-4.3.1: Email Tracking**
- Email sent timestamp
- Email opened (tracking pixel)
- Link clicks
- Reply received
- Bounce/failure

**FR-4.3.2: Response Status**
- Not Sent
- Sent
- Opened
- Confirmed
- Declined
- No Response (after 48 hours)

**FR-4.3.3: Follow-up Actions**
- Auto-reminder after 48 hours
- Escalate after 72 hours
- Flag as non-responsive after 5 days

### 3.4 Activity Timeline

**FR-4.4.1: Activity Types**
- Resume uploaded
- Status changed
- Interview scheduled
- Interview completed
- Email sent/received
- Comment added
- Rating updated
- Document uploaded

**FR-4.4.2: Timeline Display**
```
┌─────────────────────────────────────────────┐
│ Oct 6, 2025 10:30 AM                        │
│ 💬 Sarah Recruiter added a comment          │
│ "Great technical skills, moving forward"    │
│                                              │
│ Oct 5, 2025 2:00 PM                         │
│ ✅ Status changed: Shortlisted → Interview  │
│ Changed by: Sarah Recruiter                 │
│                                              │
│ Oct 5, 2025 11:15 AM                        │
│ 📅 Interview scheduled                      │
│ Technical Interview - Oct 10, 2PM           │
│ Interviewer: John Manager                   │
│                                              │
│ Oct 3, 2025 9:00 AM                         │
│ 📤 Email sent: Interview Invitation         │
│ Status: Opened (Oct 3, 10:45 AM)           │
│                                              │
│ Oct 1, 2025 4:20 PM                         │
│ 📄 Resume uploaded by Sarah Recruiter       │
│ File: john_doe_resume.pdf                   │
└─────────────────────────────────────────────┘
```

### 3.5 Notifications

**FR-4.5.1: Notification Channels**
- In-app (real-time)
- Browser push notifications
- Email (immediate or digest)
- SMS (optional, for urgent)

**FR-4.5.2: Notification Events**
- Interview scheduled (candidate + interviewers)
- Interview in 24 hours (reminder)
- Interview in 1 hour (reminder)
- Candidate response received
- Status changed
- Comment @mention
- Pending action (no activity in 3 days)

**FR-4.5.3: Notification Preferences**
```json
{
    "email_immediate": ["interview_scheduled", "candidate_response"],
    "email_daily_digest": ["status_changed", "comment_added"],
    "browser_push": ["interview_reminder", "mention"],
    "sms": ["interview_in_1_hour"],
    "mute_weekends": true,
    "quiet_hours": {
        "start": "22:00",
        "end": "08:00"
    }
}
```

---

## 4. Technical Requirements

### 4.1 Architecture

```
┌──────────────┐
│   Frontend   │
│   (React)    │
└──────┬───────┘
       │ WebSocket (real-time)
       │ REST API
       ▼
┌──────────────┐
│   FastAPI    │
│   Backend    │
└──────┬───────┘
       │
   ┌───┴───┬────────┬─────────┐
   ▼       ▼        ▼         ▼
┌──────┐┌──────┐┌──────┐┌────────┐
│ Postgres││Redis││Celery││External│
│  DB   ││Cache││ Jobs ││  APIs  │
└───────┘└──────┘└──────┘└────────┘
                          │
                    ┌─────┴──────┐
                    │            │
              ┌─────▼────┐┌─────▼────┐
              │  Google  ││Microsoft │
              │ Calendar ││  Graph   │
              └──────────┘└──────────┘
```

### 4.2 Real-Time Updates

**WebSocket Implementation:**
```python
# FastAPI WebSocket
from fastapi import WebSocket

@app.websocket("/ws/candidate/{candidate_id}")
async def websocket_endpoint(websocket: WebSocket, candidate_id: int):
    await websocket.accept()
    
    # Subscribe to candidate updates
    pubsub = redis_client.pubsub()
    pubsub.subscribe(f"candidate:{candidate_id}:updates")
    
    # Send updates to client
    for message in pubsub.listen():
        await websocket.send_json(message)
```

**Client (React):**
```javascript
const ws = new WebSocket(`ws://api/ws/candidate/${candidateId}`);

ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    // Update UI in real-time
    updateCandidateStatus(update);
};
```

### 4.3 Background Jobs

**Celery Tasks:**
```python
# Send interview invitation email
@celery.task
def send_interview_invitation(interview_id):
    interview = get_interview(interview_id)
    send_email(
        to=interview.candidate.email,
        template="interview_invitation",
        context=interview
    )
    
# Send interview reminder (scheduled 24h before)
@celery.task
def send_interview_reminder(interview_id):
    interview = get_interview(interview_id)
    if interview.status == "scheduled":
        send_email(...)
        send_notification(...)

# Check for pending actions
@celery.task(run_every=timedelta(hours=6))
def check_pending_actions():
    # Find candidates with no activity in 3 days
    candidates = find_stale_candidates(days=3)
    for candidate in candidates:
        notify_recruiter(candidate)
```

---

## 5. Database Schema

### 5.1 Candidate Status Tracking

```sql
CREATE TABLE candidate_status_history (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id),
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    changed_by INTEGER REFERENCES users(id),
    reason TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_status_history_candidate (candidate_id),
    INDEX idx_status_history_date (created_at)
);

-- Update candidates table
ALTER TABLE candidates ADD COLUMN current_status VARCHAR(50) DEFAULT 'received';
ALTER TABLE candidates ADD COLUMN status_updated_at TIMESTAMP;
ALTER TABLE candidates ADD COLUMN days_in_status INTEGER;
```

### 5.2 Interviews

```sql
CREATE TABLE interviews (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id),
    job_id INTEGER REFERENCES jobs(id),
    
    type VARCHAR(50) NOT NULL,  -- phone_screen, technical, final
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL,
    timezone VARCHAR(50) DEFAULT 'America/Los_Angeles',
    
    location VARCHAR(255),  -- Conference room or "Remote"
    meeting_link VARCHAR(500),  -- Zoom, Teams, Meet link
    
    status VARCHAR(50) DEFAULT 'scheduled',  -- scheduled, completed, cancelled, no_show
    
    notes TEXT,
    feedback TEXT,
    
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Calendar integration
    google_event_id VARCHAR(255),
    outlook_event_id VARCHAR(255),
    
    INDEX idx_interviews_candidate (candidate_id),
    INDEX idx_interviews_date (scheduled_date),
    INDEX idx_interviews_status (status)
);

CREATE TABLE interview_participants (
    interview_id INTEGER REFERENCES interviews(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(50),  -- interviewer, coordinator
    attendance_status VARCHAR(50) DEFAULT 'pending',  -- pending, confirmed, declined
    
    PRIMARY KEY (interview_id, user_id)
);
```

### 5.3 Email Tracking

```sql
CREATE TABLE email_logs (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id),
    
    email_type VARCHAR(100),  -- interview_invitation, reminder, etc.
    subject VARCHAR(500),
    body TEXT,
    
    sent_to VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP DEFAULT NOW(),
    
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    replied_at TIMESTAMP,
    bounced BOOLEAN DEFAULT FALSE,
    
    tracking_id VARCHAR(100) UNIQUE,  -- For tracking pixel
    
    INDEX idx_email_logs_candidate (candidate_id),
    INDEX idx_email_logs_tracking (tracking_id)
);
```

### 5.4 Activity Timeline

```sql
CREATE TABLE activity_log (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id),
    
    activity_type VARCHAR(100) NOT NULL,
    activity_data JSONB,
    
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_activity_candidate (candidate_id),
    INDEX idx_activity_type (activity_type),
    INDEX idx_activity_date (created_at)
);
```

### 5.5 Comments

```sql
CREATE TABLE candidate_comments (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id),
    
    comment TEXT NOT NULL,
    mentioned_users INTEGER[],  -- Array of user IDs
    attachments JSONB,  -- File URLs
    
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    
    INDEX idx_comments_candidate (candidate_id),
    INDEX idx_comments_user (created_by)
);
```

### 5.6 Notifications

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    
    type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    link VARCHAR(500),
    
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_notifications_user (user_id),
    INDEX idx_notifications_unread (user_id, is_read)
);
```

---

## 6. API Specifications

### 6.1 Update Candidate Status

**Endpoint:** `PATCH /api/candidates/{id}/status`

**Request:**
```json
{
    "status": "interviewed",
    "reason": "Passed technical round",
    "notes": "Strong performance in coding challenge"
}
```

### 6.2 Schedule Interview

**Endpoint:** `POST /api/interviews`

**Request:**
```json
{
    "candidate_id": 123,
    "job_id": 456,
    "type": "technical_interview",
    "date": "2025-10-15",
    "time": "14:00",
    "duration_minutes": 90,
    "timezone": "America/Los_Angeles",
    "location": "Zoom",
    "meeting_link": "https://zoom.us/j/123456",
    "interviewers": [5, 8],
    "notes": "Focus on system design",
    "send_calendar_invites": true
}
```

**Response:**
```json
{
    "id": 789,
    "status": "scheduled",
    "calendar_events": {
        "google": "event_id_123",
        "outlook": null
    },
    "invitations_sent": true,
    "created_at": "2025-10-06T10:30:00Z"
}
```

### 6.3 Get Activity Timeline

**Endpoint:** `GET /api/candidates/{id}/timeline`

**Response:**
```json
{
    "activities": [
        {
            "id": 1,
            "type": "comment_added",
            "data": {
                "comment": "Great technical skills",
                "author": "Sarah Recruiter"
            },
            "created_at": "2025-10-06T10:30:00Z"
        },
        {
            "id": 2,
            "type": "status_changed",
            "data": {
                "from": "shortlisted",
                "to": "interviewed",
                "changed_by": "Sarah Recruiter"
            },
            "created_at": "2025-10-05T14:00:00Z"
        }
    ]
}
```

### 6.4 Add Comment

**Endpoint:** `POST /api/candidates/{id}/comments`

**Request:**
```json
{
    "comment": "Great candidate! @john let's move forward",
    "mentioned_users": [5],
    "attachments": [
        {"filename": "notes.pdf", "url": "https://..."}
    ]
}
```

---

## 7. UI/UX Specifications

### 7.1 Kanban Board

```
┌──────────────────────────────────────────────────────────────────┐
│  📊 Candidate Pipeline                           [+ Add Filter]  │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Received(15) │ Shortlisted(8) │ Interview(5) │ Offered(2) │Hired│
│──────────────┼────────────────┼──────────────┼────────────┼─────│
│┌───────────┐ │┌───────────┐   │┌───────────┐ │┌──────────┐│     │
││John Doe   │ ││Jane Smith │   ││Bob Jones  │ ││Alice Wu  ││     │
││SWE - 7yrs │ ││SWE - 5yrs │   ││SWE - 10yrs│ ││SWE-8yrs  ││     │
││★★★★★ 4.8  │ ││★★★★☆ 4.2  │   ││★★★★★ 4.9  │ ││★★★★★4.7  ││     │
││📅 Oct 5   │ ││📅 Oct 4   │   ││📅 Oct 10  │ ││📅 Oct12  ││     │
│└───────────┘ │└───────────┘   │└───────────┘ │└──────────┘│     │
│              │                │              │            │     │
│              │                │              │            │     │
│ [+ Add]      │ [+ Add]        │ [+ Add]      │ [+ Add]    │     │
└──────────────┴────────────────┴──────────────┴────────────┴─────┘
```

### 7.2 Interview Schedule View

```
┌────────────────────────────────────────────────────────┐
│ 📅 Interview Schedule                    [+ Schedule]  │
├────────────────────────────────────────────────────────┤
│                                                         │
│ Today - October 6, 2025                                │
│ ┌──────────────────────────────────────────────────┐  │
│ │ 2:00 PM - 3:30 PM                                │  │
│ │ Technical Interview - John Doe                   │  │
│ │ 📍 Zoom Link  👤 Sarah, Mike (interviewers)      │  │
│ │ [Join] [Reschedule] [Cancel]                     │  │
│ └──────────────────────────────────────────────────┘  │
│                                                         │
│ Tomorrow - October 7, 2025                             │
│ ┌──────────────────────────────────────────────────┐  │
│ │ 10:00 AM - 11:00 AM                              │  │
│ │ Phone Screen - Jane Smith                        │  │
│ │ 📞 Phone  👤 Sarah                               │  │
│ │ [Details] [Reschedule]                           │  │
│ └──────────────────────────────────────────────────┘  │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

## 8. Implementation Plan

### Week 1: Status Pipeline
- Database schema for status tracking
- Status update API
- Activity logging

### Week 2: Interview Scheduling
- Google Calendar integration
- Outlook integration
- Interview creation API

### Week 3: Email & Notifications
- Email service setup
- Email templates
- Notification system

### Week 4: Timeline & Comments
- Activity timeline
- Comments system
- WebSocket for real-time

### Week 5: UI & Polish
- Kanban board
- Interview scheduler UI
- Testing & deployment

---

**Status:** Ready for Implementation  
**Dependencies:** Features 2, 3
