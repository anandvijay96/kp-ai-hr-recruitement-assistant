# PRD: Manual Resume Rating System

**Feature ID:** 05  
**Feature Name:** Manual Resume Rating System  
**Priority:** P1 (High)  
**Complexity:** Medium  
**Estimated Effort:** 2 weeks  
**Phase:** 2 (Tracking & Collaboration)  
**Dependencies:** Features 2, 4

---

## 1. Overview

### 1.1 Description
Allow recruiters to manually rate and evaluate candidates with star ratings, comments, and support for multiple interview rounds with complete rating history and team collaboration.

### 1.2 Business Value
- **Quality:** Structured evaluation process
- **Collaboration:** Team consensus on candidates
- **Accountability:** Track who rated what and why
- **Insights:** Analytics on rating patterns

### 1.3 Success Metrics
- Support unlimited rating rounds
- Track 100% of rating history
- Calculate average ratings accurately
- Export ratings in multiple formats

---

## 2. User Stories

### US-5.1: Rate Candidate
```
As a recruiter
I want to rate a candidate with stars and comments
So that I can record my evaluation

Acceptance Criteria:
- [ ] 1-5 star rating scale
- [ ] Required comment/justification
- [ ] Rating categories (Technical, Communication, Culture Fit)
- [ ] Save rating with timestamp
- [ ] Edit own rating within 24 hours
```

### US-5.2: Multi-Round Ratings
```
As a recruiter
I want to rate candidates for different interview rounds
So that I can track evaluation across the hiring process

Acceptance Criteria:
- [ ] Separate ratings per interview round
- [ ] Round labels (Phone Screen, Technical, Final)
- [ ] Different raters per round
- [ ] Average rating across rounds
- [ ] Visual comparison of rounds
```

### US-5.3: Team Rating Comparison
```
As a hiring manager
I want to compare ratings from multiple recruiters
So that I can see consensus and disagreements

Acceptance Criteria:
- [ ] Show all ratings side-by-side
- [ ] Highlight rating differences
- [ ] Show average team rating
- [ ] Filter by recruiter
- [ ] Export comparison report
```

### US-5.4: Rating History
```
As a recruiter
I want to see the history of rating changes
So that I have audit trail and context

Acceptance Criteria:
- [ ] Chronological rating history
- [ ] Show original vs edited ratings
- [ ] Who rated when
- [ ] Reason for rating change
- [ ] Export history
```

### US-5.5: Rating Analytics
```
As a hiring manager
I want to see rating statistics
So that I can identify patterns and improve process

Acceptance Criteria:
- [ ] Average rating by recruiter
- [ ] Rating distribution
- [ ] Time to rate
- [ ] Rating vs hire outcome correlation
```

---

## 3. Functional Requirements

### 3.1 Rating System

**FR-5.1.1: Rating Scale**
- 1 Star: Poor - Not a fit
- 2 Stars: Below Average - Weak candidate
- 3 Stars: Average - Meets basic requirements
- 4 Stars: Good - Above average candidate
- 5 Stars: Excellent - Strong hire

**FR-5.1.2: Rating Categories**
```json
{
    "technical_skills": {
        "rating": 4,
        "comment": "Strong coding skills, good system design"
    },
    "communication": {
        "rating": 5,
        "comment": "Excellent communicator, clear articulation"
    },
    "cultural_fit": {
        "rating": 4,
        "comment": "Good team player, aligns with values"
    },
    "experience": {
        "rating": 4,
        "comment": "Relevant experience, good projects"
    },
    "overall": {
        "rating": 4,  // Average of categories
        "comment": "Strong candidate, recommend hire"
    }
}
```

**FR-5.1.3: Interview Round Support**
```json
{
    "candidate_id": 123,
    "ratings": [
        {
            "round": "phone_screen",
            "round_label": "Phone Screen",
            "interview_id": 456,
            "rated_by": 5,
            "rated_at": "2025-10-05T14:30:00Z",
            "rating": 4,
            "categories": {...},
            "overall_comment": "Good initial conversation",
            "recommendation": "move_forward"
        },
        {
            "round": "technical",
            "round_label": "Technical Interview",
            "interview_id": 457,
            "rated_by": 8,
            "rated_at": "2025-10-10T10:00:00Z",
            "rating": 5,
            "categories": {...},
            "overall_comment": "Excellent technical skills",
            "recommendation": "strong_hire"
        }
    ],
    "average_rating": 4.5
}
```

### 3.2 Rating Rules

**FR-5.2.1: Permissions**
- Any recruiter can rate
- Only rating author can edit (within 24h)
- Admins can edit any rating
- Cannot delete ratings (soft delete only)

**FR-5.2.2: Validation**
- Rating (1-5) is required
- Overall comment is required (min 20 characters)
- Category ratings are optional
- Recommendation is required

**FR-5.2.3: Edit History**
- Track all edits
- Store original rating
- Require reason for edit
- Show "Edited" indicator

### 3.3 Analytics

**FR-5.3.1: Individual Recruiter Stats**
- Total ratings given
- Average rating
- Rating distribution (1-5 star breakdown)
- Most common recommendation
- Time to rate after interview

**FR-5.3.2: Candidate Rating Stats**
- Total ratings received
- Average rating
- Rating by round
- Rating by recruiter
- Rating trend (improving/declining)

**FR-5.3.3: Team Analytics**
- Inter-rater reliability
- Rating consistency
- Hire rate by rating range
- False positive/negative rates

---

## 4. Database Schema

```sql
CREATE TABLE candidate_ratings (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    interview_id INTEGER REFERENCES interviews(id),
    
    -- Round info
    round VARCHAR(100) NOT NULL,  -- phone_screen, technical, final, etc.
    round_label VARCHAR(255),
    
    -- Rating
    overall_rating DECIMAL(2,1) NOT NULL CHECK (overall_rating >= 1 AND overall_rating <= 5),
    technical_skills_rating DECIMAL(2,1),
    communication_rating DECIMAL(2,1),
    cultural_fit_rating DECIMAL(2,1),
    experience_rating DECIMAL(2,1),
    
    -- Comments
    technical_skills_comment TEXT,
    communication_comment TEXT,
    cultural_fit_comment TEXT,
    experience_comment TEXT,
    overall_comment TEXT NOT NULL,
    
    -- Recommendation
    recommendation VARCHAR(50),  -- strong_hire, hire, maybe, no_hire, strong_no_hire
    
    -- Metadata
    rated_by INTEGER REFERENCES users(id) NOT NULL,
    rated_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    is_edited BOOLEAN DEFAULT FALSE,
    edit_reason TEXT,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(id),
    
    INDEX idx_ratings_candidate (candidate_id),
    INDEX idx_ratings_interview (interview_id),
    INDEX idx_ratings_rater (rated_by),
    INDEX idx_ratings_date (rated_at)
);

CREATE TABLE rating_history (
    id SERIAL PRIMARY KEY,
    rating_id INTEGER REFERENCES candidate_ratings(id) ON DELETE CASCADE,
    
    -- Previous values
    previous_overall_rating DECIMAL(2,1),
    previous_comment TEXT,
    previous_recommendation VARCHAR(50),
    
    -- Change info
    changed_at TIMESTAMP DEFAULT NOW(),
    changed_by INTEGER REFERENCES users(id),
    change_reason TEXT,
    
    INDEX idx_rating_history_rating (rating_id)
);

-- Add aggregate rating to candidates table
ALTER TABLE candidates ADD COLUMN average_rating DECIMAL(2,1);
ALTER TABLE candidates ADD COLUMN total_ratings INTEGER DEFAULT 0;
ALTER TABLE candidates ADD COLUMN last_rated_at TIMESTAMP;

-- Trigger to update candidate average rating
CREATE OR REPLACE FUNCTION update_candidate_average_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE candidates
    SET 
        average_rating = (
            SELECT AVG(overall_rating)
            FROM candidate_ratings
            WHERE candidate_id = NEW.candidate_id
            AND is_deleted = FALSE
        ),
        total_ratings = (
            SELECT COUNT(*)
            FROM candidate_ratings
            WHERE candidate_id = NEW.candidate_id
            AND is_deleted = FALSE
        ),
        last_rated_at = NOW()
    WHERE id = NEW.candidate_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_candidate_rating
AFTER INSERT OR UPDATE ON candidate_ratings
FOR EACH ROW
EXECUTE FUNCTION update_candidate_average_rating();
```

---

## 5. API Specifications

### 5.1 Create Rating

**Endpoint:** `POST /api/candidates/{candidate_id}/ratings`

**Request:**
```json
{
    "interview_id": 456,
    "round": "technical",
    "round_label": "Technical Interview",
    "overall_rating": 4.5,
    "categories": {
        "technical_skills": {
            "rating": 5,
            "comment": "Excellent problem solving"
        },
        "communication": {
            "rating": 4,
            "comment": "Clear and concise"
        },
        "cultural_fit": {
            "rating": 4,
            "comment": "Good team player"
        }
    },
    "overall_comment": "Strong technical candidate, recommend moving forward with final round",
    "recommendation": "hire"
}
```

**Response:**
```json
{
    "id": 789,
    "candidate_id": 123,
    "overall_rating": 4.5,
    "rated_by": {
        "id": 5,
        "name": "Sarah Recruiter"
    },
    "rated_at": "2025-10-06T15:30:00Z",
    "candidate_average_rating": 4.3
}
```

### 5.2 Get Candidate Ratings

**Endpoint:** `GET /api/candidates/{candidate_id}/ratings`

**Response:**
```json
{
    "candidate_id": 123,
    "average_rating": 4.3,
    "total_ratings": 3,
    "ratings": [
        {
            "id": 789,
            "round": "technical",
            "round_label": "Technical Interview",
            "overall_rating": 4.5,
            "categories": {...},
            "overall_comment": "Strong technical candidate",
            "recommendation": "hire",
            "rated_by": {
                "id": 5,
                "name": "Sarah Recruiter"
            },
            "rated_at": "2025-10-06T15:30:00Z",
            "is_edited": false
        }
    ]
}
```

### 5.3 Update Rating

**Endpoint:** `PATCH /api/ratings/{rating_id}`

**Request:**
```json
{
    "overall_rating": 5,
    "overall_comment": "Updated: Exceptional candidate after further review",
    "edit_reason": "Reconsidered based on additional discussion"
}
```

### 5.4 Get Rating Comparison

**Endpoint:** `GET /api/candidates/{candidate_id}/ratings/comparison`

**Response:**
```json
{
    "candidate_id": 123,
    "ratings_by_round": [
        {
            "round": "phone_screen",
            "ratings": [
                {
                    "rater": "Sarah", 
                    "rating": 4,
                    "comment": "Good communication"
                }
            ],
            "average": 4.0
        },
        {
            "round": "technical",
            "ratings": [
                {
                    "rater": "Mike",
                    "rating": 5,
                    "comment": "Excellent skills"
                },
                {
                    "rater": "John",
                    "rating": 4,
                    "comment": "Good but not exceptional"
                }
            ],
            "average": 4.5
        }
    ],
    "overall_average": 4.3,
    "agreement_score": 0.85  // Inter-rater reliability
}
```

### 5.5 Export Ratings

**Endpoint:** `GET /api/candidates/{candidate_id}/ratings/export?format=csv`

**Response:** CSV file download
```csv
Candidate,Round,Rater,Rating,Technical,Communication,Culture,Comment,Date
John Doe,Phone Screen,Sarah,4.0,4,5,4,"Good candidate",2025-10-05
John Doe,Technical,Mike,5.0,5,5,5,"Excellent",2025-10-10
```

---

## 6. UI/UX Specifications

### 6.1 Rating Form

```
┌──────────────────────────────────────────────────┐
│ ⭐ Rate Candidate: John Doe                      │
│ Round: Technical Interview                       │
├──────────────────────────────────────────────────┤
│                                                   │
│ Overall Rating *                                 │
│ ☆☆☆☆☆ → ★★★★☆ (4 stars)                        │
│                                                   │
│ ── Detailed Ratings ──                           │
│                                                   │
│ Technical Skills                                 │
│ ★★★★★ (5 stars)                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Excellent problem solving ability          │ │
│ │ Strong system design knowledge             │ │
│ └─────────────────────────────────────────────┘ │
│                                                   │
│ Communication                                    │
│ ★★★★☆ (4 stars)                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Clear and articulate                       │ │
│ └─────────────────────────────────────────────┘ │
│                                                   │
│ Cultural Fit                                     │
│ ★★★★☆ (4 stars)                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Good team player, aligns with values       │ │
│ └─────────────────────────────────────────────┘ │
│                                                   │
│ Overall Comment *                                │
│ ┌─────────────────────────────────────────────┐ │
│ │ Strong technical candidate with excellent  │ │
│ │ problem-solving skills. Recommend moving   │ │
│ │ forward to final round.                    │ │
│ └─────────────────────────────────────────────┘ │
│                                                   │
│ Recommendation *                                 │
│ ○ Strong Hire  ● Hire  ○ Maybe  ○ No Hire       │
│                                                   │
│ [Cancel]  [Save Rating]                          │
│                                                   │
└──────────────────────────────────────────────────┘
```

### 6.2 Ratings Display

```
┌──────────────────────────────────────────────────┐
│ 📊 Ratings for John Doe                          │
│ Average: ★★★★☆ (4.3) | 3 ratings                │
├──────────────────────────────────────────────────┤
│                                                   │
│ Phone Screen - Oct 5, 2025                       │
│ ★★★★☆ (4.0) by Sarah Recruiter                  │
│ "Good communication skills, solid background"    │
│ Recommendation: Move Forward                     │
│ [View Details]                                   │
│                                                   │
│ ─────────────────────────────────────────────── │
│                                                   │
│ Technical Interview - Oct 10, 2025               │
│ ★★★★★ (5.0) by Mike Engineer                    │
│ "Excellent technical skills, strong hire"        │
│ Recommendation: Strong Hire                      │
│ [View Details] [Edited]                          │
│                                                   │
│ ─────────────────────────────────────────────── │
│                                                   │
│ Technical Interview - Oct 10, 2025               │
│ ★★★★☆ (4.0) by John Manager                     │
│ "Good skills, but not exceptional"               │
│ Recommendation: Hire                             │
│ [View Details]                                   │
│                                                   │
│ ─────────────────────────────────────────────── │
│                                                   │
│ [+ Add Rating] [Export Ratings] [View Comparison]│
│                                                   │
└──────────────────────────────────────────────────┘
```

### 6.3 Rating Comparison View

```
┌──────────────────────────────────────────────────────────────┐
│ 📊 Rating Comparison: John Doe                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Round           │ Phone Screen │ Technical │ Final │ Average │
│─────────────────┼──────────────┼───────────┼───────┼─────────│
│ Sarah Recruiter │ ★★★★☆ (4.0)  │     -     │   -   │  4.0   │
│ Mike Engineer   │      -       │ ★★★★★(5.0)│   -   │  5.0   │
│ John Manager    │      -       │ ★★★★☆(4.0)│   -   │  4.0   │
│─────────────────┼──────────────┼───────────┼───────┼─────────│
│ Round Average   │ 4.0          │ 4.5       │   -   │ 4.3    │
│                                                               │
│ ── Rating Details ──                                          │
│                                                               │
│ Technical Skills:     ★★★★★ (4.7)                            │
│ Communication:        ★★★★☆ (4.3)                            │
│ Cultural Fit:         ★★★★☆ (4.0)                            │
│                                                               │
│ Agreement Score: 85% (Good consistency)                       │
│                                                               │
│ [Export] [Print]                                              │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. Implementation Plan

### Week 1: Database & Backend
- Database schema
- Rating CRUD APIs
- Rating calculation logic
- Edit history tracking

### Week 2: UI & Features
- Rating form UI
- Ratings display
- Comparison view
- Export functionality
- Testing

---

**Status:** Ready for Implementation  
**Dependencies:** Features 2, 4
