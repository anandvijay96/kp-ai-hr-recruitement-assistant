# PRD: AI-Powered Resume Matching

**Feature ID:** 07  
**Feature Name:** AI-Powered Resume Matching  
**Priority:** P0 (Critical)  
**Complexity:** High  
**Estimated Effort:** 3-4 weeks  
**Phase:** 3 (Job Management & AI)  
**Dependencies:** Features 2, 6

---

## 1. Overview

### 1.1 Description
Intelligent AI system to automatically match resumes against job requirements with explainability, providing match scores, skill gap analysis, and ranking with real-time processing on uploads.

### 1.2 Business Value
- **Automation:** Reduce manual screening by 70%
- **Accuracy:** 85%+ match accuracy
- **Speed:** Process 1000 resumes in < 10 minutes
- **Insights:** Clear explanation of why candidates match

### 1.3 Success Metrics
- Match accuracy > 85% (validated by recruiters)
- Process 1000 resumes in < 10 minutes
- Provide clear match explanations
- Real-time matching on new uploads
- False positive rate < 10%

---

## 2. User Stories

### US-7.1: Auto-Match on Upload
```
As a recruiter
I want resumes to be automatically matched when uploaded
So that I immediately see best-fit candidates

Acceptance Criteria:
- [ ] Auto-match triggers on resume upload
- [ ] Match against all open jobs
- [ ] Show match score (0-100%)
- [ ] Highlight matched skills
- [ ] Identify missing skills
- [ ] Process in background
```

### US-7.2: Match Explanation
```
As a recruiter
I want to understand why a candidate matched
So that I can make informed decisions

Acceptance Criteria:
- [ ] Show match score breakdown
- [ ] Display matched skills
- [ ] Show missing skills
- [ ] Experience relevance score
- [ ] Education match indicator
- [ ] Overall recommendation
```

### US-7.3: Re-Match Candidates
```
As a recruiter
I want to re-match existing candidates against new jobs
So that I can find candidates for recently posted positions

Acceptance Criteria:
- [ ] Trigger match for specific job
- [ ] Match all candidates in database
- [ ] Show ranked results
- [ ] Filter by minimum match score
- [ ] Sort by match percentage
```

### US-7.4: Match Settings
```
As an admin
I want to configure matching algorithm weights
So that I can optimize for our hiring priorities

Acceptance Criteria:
- [ ] Adjust skill weight (0-100%)
- [ ] Adjust experience weight
- [ ] Adjust education weight
- [ ] Set minimum match threshold
- [ ] Enable/disable auto-matching
```

---

## 3. Functional Requirements

### 3.1 Matching Algorithm

**FR-7.1.1: Match Score Components**
```python
match_score = (
    skills_match * 0.40 +           # 40% weight
    experience_match * 0.30 +       # 30% weight
    education_match * 0.15 +        # 15% weight
    location_match * 0.10 +         # 10% weight
    other_factors * 0.05            # 5% weight
)
```

**FR-7.1.2: Skills Matching**
```python
# Exact match
if candidate_skill == job_skill:
    skill_score = 1.0

# Semantic similarity (using embeddings)
elif semantic_similarity(candidate_skill, job_skill) > 0.8:
    skill_score = 0.9

# Related skills
elif is_related_skill(candidate_skill, job_skill):
    skill_score = 0.7

# Calculate overall skills match
skills_match = (
    matched_mandatory_skills / total_mandatory_skills * 0.7 +
    matched_preferred_skills / total_preferred_skills * 0.3
)
```

**FR-7.1.3: Experience Matching**
```python
# Years of experience
required_years = job.min_experience
candidate_years = candidate.total_experience_years

if candidate_years >= required_years:
    experience_years_score = 1.0
elif candidate_years >= required_years * 0.8:
    experience_years_score = 0.8
else:
    experience_years_score = candidate_years / required_years

# Relevant experience
relevant_experience_score = calculate_role_relevance(
    candidate.experiences,
    job.title,
    job.responsibilities
)

experience_match = (
    experience_years_score * 0.5 +
    relevant_experience_score * 0.5
)
```

**FR-7.1.4: Education Matching**
```python
education_levels = {
    "high_school": 1,
    "associate": 2,
    "bachelor": 3,
    "master": 4,
    "phd": 5
}

required_level = education_levels.get(job.required_education)
candidate_level = education_levels.get(candidate.highest_education)

if candidate_level >= required_level:
    education_match = 1.0
elif candidate_level == required_level - 1:
    education_match = 0.7
else:
    education_match = 0.4

# Field of study bonus
if candidate.field_of_study matches job.preferred_field:
    education_match += 0.2
```

### 3.2 Explainability

**FR-7.2.1: Match Breakdown**
```json
{
    "overall_score": 85,
    "breakdown": {
        "skills": {
            "score": 90,
            "weight": 40,
            "contribution": 36,
            "details": {
                "matched_mandatory": ["Python", "Java", "AWS"],
                "missing_mandatory": ["Kubernetes"],
                "matched_preferred": ["Docker", "Redis"],
                "missing_preferred": ["Terraform"]
            }
        },
        "experience": {
            "score": 85,
            "weight": 30,
            "contribution": 25.5,
            "details": {
                "years_required": 5,
                "years_candidate": 7,
                "relevant_roles": [
                    "Senior Software Engineer at Google",
                    "Software Engineer at Microsoft"
                ]
            }
        },
        "education": {
            "score": 100,
            "weight": 15,
            "contribution": 15,
            "details": {
                "required": "Bachelor's",
                "candidate": "Master's in Computer Science",
                "field_match": true
            }
        },
        "location": {
            "score": 70,
            "weight": 10,
            "contribution": 7,
            "details": {
                "job_location": "San Francisco, CA",
                "candidate_location": "Oakland, CA",
                "distance_miles": 15,
                "remote_available": true
            }
        }
    },
    "recommendation": "strong_match",  // strong_match, good_match, maybe, weak_match
    "confidence": 0.92
}
```

### 3.3 Real-Time Matching

**FR-7.3.1: Trigger Points**
- Resume uploaded
- Job published
- Job updated (skills/requirements changed)
- Manual re-match requested

**FR-7.3.2: Background Processing**
```python
@celery.task
def match_candidate_to_jobs(candidate_id):
    candidate = get_candidate(candidate_id)
    open_jobs = get_open_jobs()
    
    matches = []
    for job in open_jobs:
        score = calculate_match_score(candidate, job)
        if score >= MINIMUM_MATCH_THRESHOLD:
            matches.append({
                "job_id": job.id,
                "score": score,
                "breakdown": get_match_breakdown(candidate, job)
            })
    
    save_match_results(candidate_id, matches)
    notify_recruiters(matches)
```

### 3.4 Ranking

**FR-7.4.1: Sort Candidates**
- By match score (highest first)
- By upload date (newest first)
- By experience (most experienced first)
- By rating (highest rated first)
- Combined score (match + rating + authenticity)

**FR-7.4.2: Shortlist Automation**
```python
# Auto-shortlist criteria
if match_score >= 85 and authenticity_score >= 70:
    auto_shortlist(candidate, job)
    notify_recruiter(candidate, job, "auto_shortlisted")
```

---

## 4. Technical Architecture

### 4.1 ML Pipeline

```
Resume Upload
    ↓
Extract Features
    ↓
┌─────────────────────────┐
│  Feature Vector         │
│  - Skills (TF-IDF)     │
│  - Experience (years)   │
│  - Education (level)    │
│  - Keywords             │
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│  Matching Engine        │
│  - Cosine Similarity    │
│  - Semantic Matching    │
│  - Rule-based Filters   │
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│  Scoring & Ranking      │
│  - Weighted Average     │
│  - Normalization        │
│  - Confidence Score     │
└─────────────────────────┘
    ↓
Match Results
```

### 4.2 Technology Stack

**NLP & Matching:**
```python
# Text processing
import spacy
nlp = spacy.load("en_core_web_lg")

# Semantic similarity
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

# TF-IDF vectorization
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Fuzzy matching
from fuzzywuzzy import fuzz
```

**Workflow:**
```python
class ResumeJobMatcher:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_lg")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def match(self, candidate, job):
        # Extract features
        candidate_features = self.extract_candidate_features(candidate)
        job_features = self.extract_job_features(job)
        
        # Calculate component scores
        skills_score = self.match_skills(
            candidate_features['skills'],
            job_features['skills']
        )
        
        experience_score = self.match_experience(
            candidate_features['experience'],
            job_features['experience_required']
        )
        
        education_score = self.match_education(
            candidate_features['education'],
            job_features['education_required']
        )
        
        # Weighted combination
        overall_score = (
            skills_score * 0.40 +
            experience_score * 0.30 +
            education_score * 0.15 +
            location_score * 0.10 +
            other_score * 0.05
        )
        
        return {
            'score': overall_score,
            'breakdown': {...},
            'confidence': self.calculate_confidence(...)
        }
```

---

## 5. Database Schema

```sql
CREATE TABLE job_candidate_matches (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    
    -- Overall match
    match_score DECIMAL(5,2) NOT NULL,  -- 0.00 - 100.00
    match_confidence DECIMAL(3,2),      -- 0.00 - 1.00
    recommendation VARCHAR(50),          -- strong_match, good_match, maybe, weak_match
    
    -- Component scores
    skills_score DECIMAL(5,2),
    experience_score DECIMAL(5,2),
    education_score DECIMAL(5,2),
    location_score DECIMAL(5,2),
    
    -- Match details (JSONB for flexibility)
    match_breakdown JSONB,
    
    -- Metadata
    matched_at TIMESTAMP DEFAULT NOW(),
    match_version VARCHAR(20),  -- Algorithm version for tracking
    
    -- Status
    is_auto_shortlisted BOOLEAN DEFAULT FALSE,
    recruiter_reviewed BOOLEAN DEFAULT FALSE,
    recruiter_feedback VARCHAR(50),  -- accurate, inaccurate
    
    UNIQUE (job_id, candidate_id),
    INDEX idx_matches_job (job_id),
    INDEX idx_matches_candidate (candidate_id),
    INDEX idx_matches_score (match_score DESC),
    INDEX idx_matches_shortlisted (is_auto_shortlisted)
);

CREATE TABLE match_algorithm_config (
    id SERIAL PRIMARY KEY,
    
    -- Weights
    skills_weight DECIMAL(3,2) DEFAULT 0.40,
    experience_weight DECIMAL(3,2) DEFAULT 0.30,
    education_weight DECIMAL(3,2) DEFAULT 0.15,
    location_weight DECIMAL(3,2) DEFAULT 0.10,
    other_weight DECIMAL(3,2) DEFAULT 0.05,
    
    -- Thresholds
    minimum_match_score DECIMAL(5,2) DEFAULT 60.00,
    auto_shortlist_threshold DECIMAL(5,2) DEFAULT 85.00,
    
    -- Features
    enable_semantic_matching BOOLEAN DEFAULT TRUE,
    enable_auto_shortlisting BOOLEAN DEFAULT TRUE,
    enable_real_time_matching BOOLEAN DEFAULT TRUE,
    
    -- Version
    version VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id)
);
```

---

## 6. API Specifications

### 6.1 Get Matches for Job

**Endpoint:** `GET /api/jobs/{job_id}/matches`

**Query Parameters:**
```
?min_score=70
&sort_by=score_desc
&page=1
&page_size=20
```

**Response:**
```json
{
    "job_id": 123,
    "total_matches": 45,
    "matches": [
        {
            "candidate_id": 456,
            "candidate_name": "John Doe",
            "match_score": 92,
            "recommendation": "strong_match",
            "skills_matched": ["Python", "Java", "AWS"],
            "skills_missing": ["Kubernetes"],
            "experience_years": 7,
            "education": "Master's in CS",
            "is_auto_shortlisted": true,
            "matched_at": "2025-10-06T10:00:00Z"
        }
    ]
}
```

### 6.2 Get Match Details

**Endpoint:** `GET /api/matches/{match_id}`

**Response:** Complete match breakdown (see FR-7.2.1)

### 6.3 Trigger Re-Match

**Endpoint:** `POST /api/jobs/{job_id}/rematch`

**Response:**
```json
{
    "job_id": 123,
    "matching_started": true,
    "candidates_to_match": 1500,
    "estimated_completion_minutes": 5
}
```

### 6.4 Update Match Config

**Endpoint:** `PATCH /api/matching/config`

**Request:**
```json
{
    "skills_weight": 0.45,
    "experience_weight": 0.30,
    "minimum_match_score": 65
}
```

---

## 7. UI/UX Specifications

### 7.1 Match Results View

```
┌──────────────────────────────────────────────────┐
│ 🎯 Matches for: Senior Software Engineer        │
│ 45 candidates matched (min score: 70%)          │
│ Sort by: [Match Score ▼] Filter: [All ▼]        │
├──────────────────────────────────────────────────┤
│                                                   │
│ ┌──────────────────────────────────────────────┐│
│ │ 92% Match - STRONG MATCH                     ││
│ │ John Doe • 7 years exp • Master's in CS      ││
│ │                                              ││
│ │ ✅ Skills: Python, Java, AWS (3/4 matched)  ││
│ │ ⚠️  Missing: Kubernetes                      ││
│ │ ✅ Experience: 7 years (5+ required)         ││
│ │ ✅ Education: Master's (Bachelor's required) ││
│ │                                              ││
│ │ [View Profile] [View Breakdown] [Shortlist] ││
│ └──────────────────────────────────────────────┘│
│                                                   │
│ ┌──────────────────────────────────────────────┐│
│ │ 78% Match - GOOD MATCH                       ││
│ │ Jane Smith • 5 years exp • Bachelor's in CS  ││
│ │                                              ││
│ │ ✅ Skills: Python, Java (2/4 matched)       ││
│ │ ⚠️  Missing: AWS, Kubernetes                 ││
│ │ ✅ Experience: 5 years (5+ required)         ││
│ │ ✅ Education: Bachelor's (required)          ││
│ │                                              ││
│ │ [View Profile] [View Breakdown] [Shortlist] ││
│ └──────────────────────────────────────────────┘│
│                                                   │
└──────────────────────────────────────────────────┘
```

### 7.2 Match Breakdown Modal

```
┌──────────────────────────────────────────────────┐
│ 📊 Match Breakdown: John Doe                     │
│ Overall Score: 92% (Strong Match)               │
├──────────────────────────────────────────────────┤
│                                                   │
│ Skills Match: 90% (40% weight → 36 points)      │
│ ████████████████████████░░░░                    │
│ Matched: Python, Java, AWS                       │
│ Missing: Kubernetes                              │
│                                                   │
│ Experience Match: 85% (30% weight → 25.5 points)│
│ ████████████████████░░░░░░░                     │
│ Required: 5+ years | Candidate: 7 years         │
│ Relevant roles: Senior SWE at Google            │
│                                                   │
│ Education Match: 100% (15% weight → 15 points)  │
│ ████████████████████████████                    │
│ Required: Bachelor's | Candidate: Master's      │
│                                                   │
│ Location Match: 70% (10% weight → 7 points)     │
│ ████████████████████░░░░░░░░░░░                 │
│ Job: San Francisco | Candidate: Oakland (15mi)  │
│                                                   │
│ Recommendation: STRONG MATCH                     │
│ Confidence: 92%                                  │
│                                                   │
│ [Close] [Shortlist Candidate]                    │
│                                                   │
└──────────────────────────────────────────────────┘
```

---

## 8. Implementation Plan

### Week 1: Feature Engineering
- Extract candidate features
- Extract job features
- Build feature vectors
- Unit tests

### Week 2: Matching Algorithm
- Skills matching (exact + semantic)
- Experience matching
- Education matching
- Location matching
- Integration tests

### Week 3: Scoring & Ranking
- Weighted scoring
- Confidence calculation
- Explainability
- Performance optimization

### Week 4: UI & Integration
- Match results UI
- Match breakdown view
- Real-time matching
- E2E tests

---

**Status:** Ready for Implementation  
**Dependencies:** Features 2, 6  
**Key Risk:** ML accuracy - requires continuous tuning and feedback
