# PRD: Advanced Resume Filtering

**Feature ID:** 03  
**Feature Name:** Advanced Resume Filtering  
**Priority:** P0 (Critical)  
**Complexity:** Medium  
**Estimated Effort:** 2-3 weeks  
**Phase:** 1 (Foundation)  
**Dependencies:** Feature 2 (Resume Upload)

---

## 1. Overview

### 1.1 Description
Powerful search and filter system enabling recruiters to quickly find candidates using multiple criteria including skills, experience, education, location, ratings, and boolean operators.

### 1.2 Business Value
- **Efficiency:** Reduce candidate search time by 80%
- **Precision:** Find exact matches in < 2 seconds from 10,000+ resumes
- **Flexibility:** Support complex queries with boolean logic
- **Productivity:** Save and reuse common filter combinations

### 1.3 Success Metrics
- Search results returned in < 2 seconds
- Support 10,000+ candidate database
- 95%+ user satisfaction with search relevance
- 50%+ reduction in time to find candidates

---

## 2. User Stories

### US-3.1: Skill-Based Filtering
```
As a recruiter
I want to filter candidates by specific skills
So that I can find technically qualified candidates

Acceptance Criteria:
- [ ] Multi-select skill filter
- [ ] AND/OR logic for skills
- [ ] Show match percentage
- [ ] Support partial skill matching
- [ ] Display skill count per candidate
```

### US-3.2: Experience Filtering
```
As a recruiter
I want to filter by years of experience
So that I can find candidates at the right seniority level

Acceptance Criteria:
- [ ] Min-max year range slider
- [ ] Filter by total experience
- [ ] Filter by experience in specific role/company
- [ ] Show experience breakdown
```

### US-3.3: Education Filtering
```
As a recruiter
I want to filter by education qualification
So that I can find candidates with required degrees

Acceptance Criteria:
- [ ] Filter by degree level (Bachelor's, Master's, PhD)
- [ ] Filter by field of study
- [ ] Filter by institution
- [ ] Filter by GPA (if available)
```

### US-3.4: Boolean Search
```
As a recruiter
I want to use boolean operators in search
So that I can create complex queries

Acceptance Criteria:
- [ ] Support AND operator
- [ ] Support OR operator
- [ ] Support NOT operator
- [ ] Support parentheses for grouping
- [ ] Provide query builder UI
- [ ] Show query syntax help
```

### US-3.5: Save Filter Presets
```
As a recruiter
I want to save my commonly used filters
So that I can reuse them without recreating

Acceptance Criteria:
- [ ] Save filter as preset
- [ ] Name and describe presets
- [ ] Load saved presets
- [ ] Edit existing presets
- [ ] Delete presets
- [ ] Share presets with team
```

---

## 3. Functional Requirements

### 3.1 Filter Categories

**FR-3.1.1: Skills Filter**
- Multi-select dropdown with search
- Display skill categories
- Show candidate count per skill
- Support "Any of" (OR) and "All of" (AND) logic

**FR-3.1.2: Experience Filter**
- Min-max range slider (0-30+ years)
- Quick filters: 0-2, 2-5, 5-10, 10+ years
- Filter by current/past companies
- Filter by specific job titles

**FR-3.1.3: Education Filter**
- Degree level: High School, Associate, Bachelor's, Master's, PhD
- Field of study (autocomplete)
- Institution name (autocomplete)
- GPA range (if available)

**FR-3.1.4: Location & Availability**
- City/State/Country filter
- Radius search (within X miles)
- Remote work preference
- Relocation willingness

**FR-3.1.5: Rating Filter**
- Filter by star rating (1-5)
- Filter by rating source (manual, AI)
- Filter by average rating
- Filter by specific recruiter ratings

**FR-3.1.6: Status Filter**
- New, Screened, Interviewed, Offered, Hired, Rejected
- Multi-select with counts
- Date range for status change

### 3.2 Search Features

**FR-3.2.1: Full-Text Search**
- Search across all candidate data
- Keyword highlighting in results
- Relevance scoring
- Fuzzy matching for typos

**FR-3.2.2: Boolean Operators**
```
Examples:
- Python AND Java
- (Python OR Java) AND NOT Junior
- "Machine Learning" AND (AWS OR Azure)
- Senior AND (Developer OR Engineer)
```

**FR-3.2.3: Advanced Filters**
- Date added range
- Last updated range
- Resume file type
- Resume upload source
- Assigned recruiter

### 3.3 Results Display

**FR-3.3.1: Result List**
- Paginated results (20 per page)
- Sort options:
  - Relevance (default)
  - Name (A-Z, Z-A)
  - Experience (high to low, low to high)
  - Rating (high to low)
  - Date added (newest, oldest)
- Quick view card with key info
- Bulk select for actions

**FR-3.3.2: Result Actions**
- View full candidate profile
- Add to shortlist
- Change status
- Add tags
- Export selected
- Share with team

---

## 4. Technical Requirements

### 4.1 Search Technology

**Option 1: PostgreSQL Full-Text Search (Recommended for MVP)**
```sql
-- Create search index
CREATE INDEX idx_candidates_search ON candidates 
USING GIN (to_tsvector('english', 
    full_name || ' ' || 
    COALESCE(email, '') || ' ' ||
    COALESCE(location, '')
));

-- Search query
SELECT * FROM candidates
WHERE search_vector @@ to_tsquery('english', 'python & java');
```

**Pros:**
- Built into PostgreSQL
- Good performance (< 100ms for 100K records)
- No additional infrastructure
- Easy to maintain

**Cons:**
- Limited to basic text search
- No advanced relevance tuning

**Option 2: Elasticsearch (For Scale)**
- Better for > 100K records
- Advanced relevance scoring
- Faceted search
- Requires additional infrastructure

**Decision:** Start with PostgreSQL FTS, migrate to Elasticsearch if needed

### 4.2 Filter Implementation

**Backend (FastAPI):**
```python
class CandidateFilterService:
    def filter_candidates(
        self,
        skills: List[str] = None,
        min_experience: int = None,
        max_experience: int = None,
        education: List[str] = None,
        location: str = None,
        rating_min: float = None,
        status: List[str] = None,
        search_query: str = None,
        sort_by: str = "relevance",
        page: int = 1,
        page_size: int = 20
    ) -> FilterResult:
        # Build dynamic query
        query = self.build_query(filters)
        
        # Execute with pagination
        results = query.offset((page-1)*page_size).limit(page_size).all()
        
        # Calculate facets
        facets = self.calculate_facets(filters)
        
        return FilterResult(
            results=results,
            total=total_count,
            facets=facets,
            page=page
        )
```

### 4.3 Performance Optimization

**Database Indexes:**
```sql
CREATE INDEX idx_candidates_skills ON candidate_skills(skill_id);
CREATE INDEX idx_candidates_experience ON candidates(total_experience_months);
CREATE INDEX idx_candidates_status ON candidates(status);
CREATE INDEX idx_candidates_rating ON candidates(average_rating);
CREATE INDEX idx_education_degree ON education(degree);
```

**Caching Strategy:**
```python
# Cache filter options (skills list, etc.)
@cache.memoize(timeout=300)  # 5 minutes
def get_filter_options():
    return {
        "skills": get_all_skills(),
        "locations": get_all_locations(),
        "companies": get_all_companies()
    }

# Cache search results briefly
@cache.memoize(timeout=60)  # 1 minute
def search_candidates(filters_hash):
    return execute_search(filters)
```

---

## 5. Database Schema

### 5.1 Filter Presets

```sql
CREATE TABLE filter_presets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    filters JSONB NOT NULL,  -- Stored filter criteria
    is_shared BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_filter_presets_user (user_id),
    INDEX idx_filter_presets_shared (is_shared)
);
```

**Example filters JSON:**
```json
{
    "skills": ["Python", "Java"],
    "skills_logic": "AND",
    "min_experience": 5,
    "max_experience": 10,
    "education": ["Bachelor's", "Master's"],
    "location": "San Francisco, CA",
    "rating_min": 4.0,
    "status": ["new", "screened"],
    "search_query": "machine learning"
}
```

### 5.2 Search Analytics

```sql
CREATE TABLE search_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    search_query TEXT,
    filters JSONB,
    result_count INTEGER,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_search_analytics_user (user_id),
    INDEX idx_search_analytics_date (created_at)
);
```

---

## 6. API Specifications

### 6.1 Search/Filter Candidates

**Endpoint:** `GET /api/candidates/search`

**Query Parameters:**
```
?skills=Python,Java
&skills_logic=AND
&min_experience=5
&max_experience=10
&education=Bachelor's,Master's
&location=San Francisco
&rating_min=4.0
&status=new,screened
&search=machine learning
&sort_by=relevance
&page=1
&page_size=20
```

**Response:**
```json
{
    "results": [
        {
            "id": 123,
            "name": "John Doe",
            "email": "john@example.com",
            "skills": ["Python", "Java", "AWS"],
            "total_experience_years": 7,
            "education": "Master's in CS",
            "location": "San Francisco, CA",
            "rating": 4.5,
            "status": "screened",
            "match_score": 0.95
        }
    ],
    "pagination": {
        "total": 150,
        "page": 1,
        "page_size": 20,
        "total_pages": 8
    },
    "facets": {
        "skills": {
            "Python": 120,
            "Java": 85,
            "JavaScript": 95
        },
        "experience_ranges": {
            "0-2": 25,
            "2-5": 45,
            "5-10": 50,
            "10+": 30
        },
        "status": {
            "new": 60,
            "screened": 50,
            "interviewed": 40
        }
    },
    "execution_time_ms": 145
}
```

### 6.2 Get Filter Options

**Endpoint:** `GET /api/candidates/filter-options`

**Response:**
```json
{
    "skills": [
        {"id": 1, "name": "Python", "count": 250},
        {"id": 2, "name": "Java", "count": 180}
    ],
    "locations": [
        {"name": "San Francisco, CA", "count": 120},
        {"name": "New York, NY", "count": 95}
    ],
    "companies": [
        {"name": "Google", "count": 45},
        {"name": "Microsoft", "count": 38}
    ],
    "education_levels": [
        {"name": "Bachelor's", "count": 350},
        {"name": "Master's", "count": 180}
    ]
}
```

### 6.3 Save Filter Preset

**Endpoint:** `POST /api/filter-presets`

**Request:**
```json
{
    "name": "Senior Python Developers",
    "description": "Python devs with 5+ years experience",
    "filters": {
        "skills": ["Python"],
        "min_experience": 5,
        "status": ["new", "screened"]
    },
    "is_shared": false
}
```

### 6.4 Get Filter Presets

**Endpoint:** `GET /api/filter-presets`

**Response:**
```json
{
    "presets": [
        {
            "id": 1,
            "name": "Senior Python Developers",
            "description": "Python devs with 5+ years",
            "filters": {...},
            "is_shared": false,
            "created_at": "2025-10-01T10:00:00Z"
        }
    ]
}
```

---

## 7. UI/UX Specifications

### 7.1 Filter Panel (Left Sidebar)

```
┌─────────────────────────────────┐
│ 🔍 Search Candidates            │
├─────────────────────────────────┤
│                                  │
│ [Search keywords...]             │
│                                  │
│ ▼ Skills                         │
│ ┌─────────────────────────────┐ │
│ │ [Search skills...]          │ │
│ │ ☑ Python (250)              │ │
│ │ ☑ Java (180)                │ │
│ │ ☐ JavaScript (195)          │ │
│ └─────────────────────────────┘ │
│ ○ Match Any  ● Match All        │
│                                  │
│ ▼ Experience                     │
│ ├──────────────────────────┤    │
│ 0   5   10   15   20   25   30+ │
│ Min: 5 years  Max: 10 years     │
│                                  │
│ ▼ Education                      │
│ ☐ High School                    │
│ ☑ Bachelor's (350)               │
│ ☑ Master's (180)                 │
│ ☐ PhD (45)                       │
│                                  │
│ ▼ Location                       │
│ [Search location...]             │
│ Within [50] miles                │
│                                  │
│ ▼ Rating                         │
│ Min: ★★★★☆ (4.0)                │
│                                  │
│ ▼ Status                         │
│ ☑ New (60)                       │
│ ☑ Screened (50)                  │
│ ☐ Interviewed (40)               │
│                                  │
│ [Clear All] [Apply Filters]      │
│ [Save as Preset]                 │
│                                  │
└─────────────────────────────────┘
```

### 7.2 Results View

```
┌────────────────────────────────────────────────────────────┐
│ Showing 1-20 of 150 results                   Sort by: [▼] │
│ [Export Selected]  [Bulk Actions ▼]                        │
├────────────────────────────────────────────────────────────┤
│                                                             │
│ ☐ John Doe                                    ★★★★★ (4.8) │
│   Senior Software Engineer | 7 years exp                   │
│   📍 San Francisco, CA | 📧 john@example.com              │
│   Skills: Python, Java, AWS, Docker                        │
│   Status: Screened | Added: Oct 1, 2025                    │
│   [View Profile] [Shortlist] [Change Status]               │
│                                                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│ ☐ Jane Smith                                  ★★★★☆ (4.2) │
│   Software Engineer | 5 years exp                          │
│   📍 New York, NY | 📧 jane@example.com                   │
│   Skills: Python, JavaScript, React, Node.js               │
│   Status: New | Added: Oct 5, 2025                         │
│   [View Profile] [Shortlist] [Change Status]               │
│                                                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│ ... more results ...                                        │
│                                                             │
├────────────────────────────────────────────────────────────┤
│ [◄ Previous]  1  2  3  4  5  ...  8  [Next ►]             │
└────────────────────────────────────────────────────────────┘
```

### 7.3 Boolean Query Builder

```
┌──────────────────────────────────────────────────────────┐
│ 🔧 Advanced Query Builder                                │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ ┌─ Rule Group (AND) ────────────────────────────┐       │
│ │                                                 │       │
│ │  Skill  [contains]  [Python          ▼] [×]   │       │
│ │  [+ AND]  [+ OR]                               │       │
│ │                                                 │       │
│ │  ┌─ Rule Group (OR) ──────────────────┐       │       │
│ │  │                                      │       │       │
│ │  │  Skill [contains] [Java    ▼] [×]  │       │       │
│ │  │  [OR]                                │       │       │
│ │  │  Skill [contains] [C++     ▼] [×]  │       │       │
│ │  │                                      │       │       │
│ │  │  [+ AND]  [+ OR]                    │       │       │
│ │  └────────────────────────────────────┘       │       │
│ │                                                 │       │
│ │  [NOT]                                         │       │
│ │  Title  [contains]  [Junior          ▼] [×]   │       │
│ │                                                 │       │
│ │  [+ AND]  [+ OR]  [+ NOT]                     │       │
│ └───────────────────────────────────────────────┘       │
│                                                           │
│ Query Preview:                                            │
│ (Skill:Python) AND (Skill:Java OR Skill:C++) AND         │
│ NOT (Title:Junior)                                        │
│                                                           │
│ [Apply Query]  [Save as Preset]  [Clear]                │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 8. Implementation Plan

### Week 1: Backend Foundation
- Day 1-2: Database schema and indexes
- Day 3-4: Filter service implementation
- Day 5: API endpoints

### Week 2: Search & Performance
- Day 1-2: PostgreSQL full-text search setup
- Day 3-4: Boolean query parser
- Day 5: Performance optimization & caching

### Week 3: UI & Polish
- Day 1-2: Filter panel UI
- Day 3-4: Results display & pagination
- Day 5: Filter presets feature

---

## 9. Testing Strategy

**Unit Tests:**
- Filter query builder
- Boolean parser
- Pagination logic

**Integration Tests:**
- Filter API endpoints
- Search performance
- Preset save/load

**E2E Tests:**
- Complete search workflow
- Boolean query execution
- Filter preset usage

---

**Status:** Ready for Implementation  
**Dependencies:** Feature 2 (Resume Upload) must be complete
