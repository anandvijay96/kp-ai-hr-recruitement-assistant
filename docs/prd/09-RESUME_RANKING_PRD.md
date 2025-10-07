# PRD: Resume Match Rating & Ranking

**Feature ID:** 09  
**Feature Name:** Resume Match Rating & Ranking  
**Priority:** P1 (High)  
**Complexity:** Medium  
**Estimated Effort:** 2 weeks  
**Phase:** 4 (Advanced Features)  
**Dependencies:** Features 5, 7

---

## 1. Overview

### 1.1 Description
Advanced ranking system that combines AI match scores with manual ratings to create a composite score for optimal candidate selection, with configurable weights and side-by-side comparison capabilities.

### 1.2 Business Value
- **Better Decisions:** Combine AI and human judgment
- **Objectivity:** Standardized scoring reduces bias
- **Efficiency:** Quickly identify top candidates
- **Transparency:** Clear scoring methodology

### 1.3 Success Metrics
- Accurate composite scoring
- Configurable weight system working
- Real-time ranking updates
- Export rankings in multiple formats
- Visual comparison view functional

---

## 2. User Stories

### US-9.1: View Ranked Candidates
```
As a recruiter
I want to see candidates ranked by composite score
So that I can prioritize my review

Acceptance Criteria:
- [ ] Sort by composite score
- [ ] Show score breakdown
- [ ] Filter by minimum score
- [ ] Highlight top 5 candidates
- [ ] Export ranked list
```

### US-9.2: Configure Ranking Weights
```
As a hiring manager
I want to configure ranking weights
So that I can prioritize what matters for this role

Acceptance Criteria:
- [ ] Adjust AI match weight (0-100%)
- [ ] Adjust manual rating weight
- [ ] Adjust authenticity score weight
- [ ] Preview score changes
- [ ] Save custom weight profiles
```

### US-9.3: Compare Candidates
```
As a recruiter
I want to compare candidates side-by-side
So that I can make better decisions

Acceptance Criteria:
- [ ] Select 2-5 candidates
- [ ] View scores side-by-side
- [ ] Compare skills, experience, education
- [ ] See rating differences
- [ ] Export comparison
```

### US-9.4: Top Candidates Recommendation
```
As a recruiter
I want to see top 5 recommended candidates
So that I can quickly start with best fits

Acceptance Criteria:
- [ ] Auto-highlight top 5
- [ ] Show recommendation reason
- [ ] One-click shortlist
- [ ] Track recommendation accuracy
```

---

## 3. Functional Requirements

### 3.1 Composite Scoring

**FR-9.1.1: Score Components**
```python
composite_score = (
    ai_match_score * match_weight +          # Default: 40%
    manual_rating * rating_weight +          # Default: 30%
    authenticity_score * authenticity_weight +  # Default: 20%
    experience_factor * experience_weight    # Default: 10%
)

# Normalize to 0-100
composite_score = min(100, max(0, composite_score))
```

**FR-9.1.2: Default Weights**
```json
{
    "weights": {
        "ai_match_score": 0.40,      // 40%
        "manual_rating": 0.30,       // 30%
        "authenticity_score": 0.20,  // 20%
        "experience_factor": 0.10    // 10%
    },
    "minimum_threshold": 60,         // Don't show below 60%
    "auto_shortlist_threshold": 85   // Auto-shortlist above 85%
}
```

**FR-9.1.3: Multi-Criteria Scoring**
```json
{
    "candidate_id": 123,
    "job_id": 456,
    "composite_score": 87.5,
    
    "breakdown": {
        "ai_match": {
            "score": 92,
            "weight": 40,
            "contribution": 36.8
        },
        "manual_rating": {
            "score": 85,
            "weight": 30,
            "contribution": 25.5
        },
        "authenticity": {
            "score": 78,
            "weight": 20,
            "contribution": 15.6
        },
        "experience": {
            "score": 95,  // 7 years vs 5 required
            "weight": 10,
            "contribution": 9.5
        }
    },
    
    "ranking": {
        "rank": 2,
        "total_candidates": 87,
        "percentile": 98
    },
    
    "recommendation": "strong_hire",
    "auto_shortlisted": true
}
```

### 3.2 Ranking Logic

**FR-9.2.1: Sort Options**
- Composite score (default)
- AI match score only
- Manual rating only
- Experience (years)
- Education level
- Date applied (newest/oldest)

**FR-9.2.2: Filtering**
- Minimum composite score
- Minimum AI match score
- Minimum manual rating
- Minimum authenticity score
- Experience range
- Education level

**FR-9.2.3: Grouping**
```
Strong Hire (85-100):  [5 candidates]
Good Fit (70-84):      [15 candidates]
Maybe (60-69):         [30 candidates]
Weak Fit (<60):        [37 candidates]
```

### 3.3 Comparison Features

**FR-9.3.1: Side-by-Side Comparison**
```json
{
    "candidates": [
        {
            "id": 123,
            "name": "John Doe",
            "composite_score": 92,
            "ai_match": 95,
            "rating": 90,
            "authenticity": 85,
            "skills": ["Python", "Java", "AWS"],
            "experience_years": 7,
            "education": "Master's"
        },
        {
            "id": 124,
            "name": "Jane Smith",
            "composite_score": 88,
            "ai_match": 90,
            "rating": 85,
            "authenticity": 90,
            "skills": ["Python", "JavaScript", "React"],
            "experience_years": 5,
            "education": "Bachelor's"
        }
    ],
    "comparison": {
        "winner": 123,
        "score_difference": 4,
        "key_differences": [
            "John has 2 more years experience",
            "John has higher AI match (95 vs 90)",
            "Jane has higher authenticity (90 vs 85)"
        ]
    }
}
```

### 3.4 Weight Profiles

**FR-9.4.1: Custom Weight Profiles**
```json
{
    "profiles": [
        {
            "id": 1,
            "name": "Technical Roles",
            "weights": {
                "ai_match_score": 0.50,
                "manual_rating": 0.25,
                "authenticity_score": 0.15,
                "experience_factor": 0.10
            }
        },
        {
            "id": 2,
            "name": "Leadership Roles",
            "weights": {
                "ai_match_score": 0.30,
                "manual_rating": 0.40,
                "authenticity_score": 0.15,
                "experience_factor": 0.15
            }
        },
        {
            "id": 3,
            "name": "Entry Level",
            "weights": {
                "ai_match_score": 0.45,
                "manual_rating": 0.30,
                "authenticity_score": 0.20,
                "experience_factor": 0.05
            }
        }
    ]
}
```

---

## 4. Database Schema

```sql
CREATE TABLE ranking_weights (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),  -- NULL for global
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Weights (must sum to 1.0)
    ai_match_weight DECIMAL(3,2) DEFAULT 0.40,
    manual_rating_weight DECIMAL(3,2) DEFAULT 0.30,
    authenticity_weight DECIMAL(3,2) DEFAULT 0.20,
    experience_weight DECIMAL(3,2) DEFAULT 0.10,
    
    -- Thresholds
    minimum_threshold DECIMAL(5,2) DEFAULT 60.00,
    auto_shortlist_threshold DECIMAL(5,2) DEFAULT 85.00,
    
    is_default BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_ranking_weights_job (job_id)
);

CREATE TABLE candidate_composite_scores (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    
    -- Component scores
    ai_match_score DECIMAL(5,2),
    manual_rating_score DECIMAL(5,2),
    authenticity_score DECIMAL(5,2),
    experience_score DECIMAL(5,2),
    
    -- Composite
    composite_score DECIMAL(5,2) NOT NULL,
    
    -- Ranking
    rank INTEGER,
    total_candidates INTEGER,
    percentile DECIMAL(5,2),
    
    -- Categorization
    score_category VARCHAR(50),  -- strong_hire, good_fit, maybe, weak_fit
    
    -- Auto actions
    is_auto_shortlisted BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    calculated_at TIMESTAMP DEFAULT NOW(),
    weight_profile_id INTEGER REFERENCES ranking_weights(id),
    
    UNIQUE (candidate_id, job_id),
    INDEX idx_composite_scores_job (job_id),
    INDEX idx_composite_scores_score (composite_score DESC),
    INDEX idx_composite_scores_rank (job_id, rank)
);

-- Trigger to update composite scores when components change
CREATE OR REPLACE FUNCTION update_composite_score()
RETURNS TRIGGER AS $$
DECLARE
    weights RECORD;
BEGIN
    -- Get applicable weights
    SELECT * INTO weights
    FROM ranking_weights
    WHERE (job_id = NEW.job_id OR job_id IS NULL)
    AND is_default = TRUE
    LIMIT 1;
    
    -- Calculate composite score
    NEW.composite_score := (
        COALESCE(NEW.ai_match_score, 0) * weights.ai_match_weight +
        COALESCE(NEW.manual_rating_score, 0) * weights.manual_rating_weight +
        COALESCE(NEW.authenticity_score, 0) * weights.authenticity_weight +
        COALESCE(NEW.experience_score, 0) * weights.experience_weight
    );
    
    -- Categorize
    NEW.score_category := CASE
        WHEN NEW.composite_score >= 85 THEN 'strong_hire'
        WHEN NEW.composite_score >= 70 THEN 'good_fit'
        WHEN NEW.composite_score >= 60 THEN 'maybe'
        ELSE 'weak_fit'
    END;
    
    -- Auto-shortlist
    IF NEW.composite_score >= weights.auto_shortlist_threshold THEN
        NEW.is_auto_shortlisted := TRUE;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_composite_score
BEFORE INSERT OR UPDATE ON candidate_composite_scores
FOR EACH ROW
EXECUTE FUNCTION update_composite_score();
```

---

## 5. API Specifications

### 5.1 Get Ranked Candidates

**Endpoint:** `GET /api/jobs/{job_id}/candidates/ranked`

**Query Parameters:**
```
?min_score=60
&sort_by=composite_desc
&category=strong_hire,good_fit
&page=1
&page_size=20
```

**Response:**
```json
{
    "job_id": 123,
    "total_candidates": 87,
    "filtered_count": 20,
    "candidates": [
        {
            "candidate_id": 456,
            "name": "John Doe",
            "composite_score": 92.5,
            "rank": 1,
            "percentile": 99,
            "category": "strong_hire",
            "breakdown": {
                "ai_match": {"score": 95, "contribution": 38},
                "rating": {"score": 90, "contribution": 27},
                "authenticity": {"score": 85, "contribution": 17},
                "experience": {"score": 100, "contribution": 10}
            },
            "is_auto_shortlisted": true
        }
    ]
}
```

### 5.2 Compare Candidates

**Endpoint:** `POST /api/candidates/compare`

**Request:**
```json
{
    "job_id": 123,
    "candidate_ids": [456, 457, 458]
}
```

**Response:**
```json
{
    "job_id": 123,
    "candidates": [...],  // Full details for each
    "comparison_matrix": {
        "composite_score": [92, 88, 85],
        "ai_match": [95, 90, 87],
        "rating": [90, 85, 88],
        "authenticity": [85, 90, 80]
    },
    "winner": {
        "candidate_id": 456,
        "name": "John Doe",
        "reasons": [
            "Highest composite score (92)",
            "Highest AI match (95)",
            "Most experience (7 years)"
        ]
    }
}
```

### 5.3 Update Ranking Weights

**Endpoint:** `PATCH /api/jobs/{job_id}/ranking-weights`

**Request:**
```json
{
    "ai_match_weight": 0.50,
    "manual_rating_weight": 0.25,
    "authenticity_weight": 0.15,
    "experience_weight": 0.10,
    "minimum_threshold": 65
}
```

**Response:**
```json
{
    "job_id": 123,
    "weights_updated": true,
    "candidates_reranked": 87,
    "new_top_5": [456, 457, 458, 459, 460]
}
```

### 5.4 Export Ranked List

**Endpoint:** `GET /api/jobs/{job_id}/candidates/export?format=csv`

**Response:** CSV download
```csv
Rank,Name,Composite Score,AI Match,Rating,Authenticity,Experience,Category
1,John Doe,92.5,95,90,85,7 years,Strong Hire
2,Jane Smith,88.0,90,85,90,5 years,Strong Hire
3,Bob Jones,85.5,87,88,80,10 years,Strong Hire
```

---

## 6. UI/UX Specifications

### 6.1 Ranked Candidates List

```
┌──────────────────────────────────────────────────────────┐
│ 🏆 Ranked Candidates: Senior Software Engineer          │
│ 87 candidates • Showing top 20                          │
│ Weights: [Customize ▼]                                   │
├──────────────────────────────────────────────────────────┤
│ ┌─ Strong Hire (85-100) ─── 5 candidates ─────────────┐ │
│ │                                                        │ │
│ │ #1  John Doe                      92.5  🌟 Top Pick  │ │
│ │     ████████████████████░                             │ │
│ │     AI: 95 | Rating: 90 | Auth: 85 | Exp: 7y         │ │
│ │     [View] [Compare] [Shortlist]                      │ │
│ │                                                        │ │
│ │ #2  Jane Smith                    88.0               │ │
│ │     ████████████████████                              │ │
│ │     AI: 90 | Rating: 85 | Auth: 90 | Exp: 5y         │ │
│ │     [View] [Compare] [Shortlist]                      │ │
│ │                                                        │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                           │
│ ┌─ Good Fit (70-84) ─── 15 candidates ────────────────┐ │
│ │                                                        │ │
│ │ #6  Bob Jones                     78.5               │ │
│ │     ████████████████                                  │ │
│ │     AI: 80 | Rating: 75 | Auth: 82 | Exp: 10y        │ │
│ │     [View] [Compare] [Shortlist]                      │ │
│ │                                                        │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                           │
│ [Export List] [Bulk Shortlist Top 5] [1][2][3][4]       │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 6.2 Weight Customization

```
┌──────────────────────────────────────────────────────────┐
│ ⚖️ Customize Ranking Weights                             │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ AI Match Score (40%)                                     │
│ ├────────────────────────────────┤                       │
│ 0%                     50%                     100%      │
│                                                           │
│ Manual Rating (30%)                                      │
│ ├──────────────────────────┤                             │
│ 0%                     50%                     100%      │
│                                                           │
│ Authenticity Score (20%)                                 │
│ ├──────────────────┤                                     │
│ 0%                     50%                     100%      │
│                                                           │
│ Experience Factor (10%)                                  │
│ ├──────┤                                                 │
│ 0%                     50%                     100%      │
│                                                           │
│ Total: 100% ✓                                            │
│                                                           │
│ ── Preview Impact ──                                      │
│ Top 5 will change:                                       │
│ • John Doe: #1 → #1 (no change)                         │
│ • Jane Smith: #2 → #3 (↓1)                              │
│ • Bob Jones: #6 → #2 (↑4)                               │
│                                                           │
│ [Cancel] [Save & Apply] [Save as Profile]               │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 6.3 Candidate Comparison

```
┌──────────────────────────────────────────────────────────┐
│ ⚖️ Compare Candidates                                     │
├─────────────┬─────────────┬─────────────┬──────────────┤
│   Metric    │  John Doe   │ Jane Smith  │  Bob Jones   │
├─────────────┼─────────────┼─────────────┼──────────────┤
│ Composite   │  92.5 🥇    │    88.0     │    78.5      │
│ AI Match    │  95 🥇      │    90       │    80        │
│ Rating      │  90         │    85       │    75 🥉     │
│ Authenticity│  85         │    90 🥇    │    82        │
│ Experience  │  7 years    │  5 years    │  10 years 🥇 │
│ Education   │  Master's🥇 │  Bachelor's │  Bachelor's  │
├─────────────┼─────────────┼─────────────┼──────────────┤
│ Skills      │ Python      │ Python      │ Python       │
│ Matched     │ Java        │ JavaScript  │ Java         │
│             │ AWS  🥇     │ React       │ C++          │
├─────────────┼─────────────┼─────────────┼──────────────┤
│ Recommended │ ✅ Yes      │ ✅ Yes      │ Maybe        │
│                                                           │
│ Winner: John Doe (highest composite score)               │
│ Key Strengths: AI match, Education, AWS expertise        │
│                                                           │
│ [Export Comparison] [Shortlist All]                      │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 7. Implementation Plan

### Week 1: Scoring Engine
- Composite scoring algorithm
- Weight management
- Database schema
- API endpoints

### Week 2: UI & Features
- Ranked list view
- Weight customization UI
- Comparison view
- Export functionality
- Testing

---

**Status:** Ready for Implementation  
**Dependencies:** Features 5 (Rating), 7 (AI Matching)  
**Key Feature:** Combines AI and human judgment for better hiring decisions
