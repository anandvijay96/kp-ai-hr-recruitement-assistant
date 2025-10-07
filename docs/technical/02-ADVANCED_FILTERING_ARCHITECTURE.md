# Technical Architecture: Advanced Resume Filtering

**Document Status:** Draft

---

## 1. DATABASE DESIGN

### 1.1. Table Modifications

We will augment the existing `candidates` table and add a new table for filter presets.

**`candidates` table (additions)**
- `total_experience_months` (INTEGER) - To be populated during resume processing.
- `average_rating` (DECIMAL(3, 2)) - For filtering by rating.
- `status` (VARCHAR(50)) - To filter by candidate status.
- `search_vector` (TSVECTOR) - For full-text search.

**New table: `filter_presets`**
- `id`: `SERIAL PRIMARY KEY`
- `user_id`: `INTEGER REFERENCES users(id)` (Assuming a `users` table exists)
- `name`: `VARCHAR(255) NOT NULL`
- `description`: `TEXT`
- `filters`: `JSONB NOT NULL`
- `is_shared`: `BOOLEAN DEFAULT FALSE`
- `created_at`: `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`

### 1.2. Indexes

To ensure fast query performance, the following indexes will be created:

- `CREATE INDEX idx_candidates_experience ON candidates(total_experience_months);`
- `CREATE INDEX idx_candidates_status ON candidates(status);`
- `CREATE INDEX idx_candidates_rating ON candidates(average_rating);`
- `CREATE INDEX idx_candidates_search ON candidates USING GIN(search_vector);`

---

## 2. API DESIGN

### 2.1. Pydantic Models

```python
# In a new file: models/filter_models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class CandidateFilter(BaseModel):
    skills: Optional[List[str]] = None
    skills_logic: str = 'AND'
    min_experience: Optional[int] = None
    max_experience: Optional[int] = None
    education: Optional[List[str]] = None
    location: Optional[str] = None
    rating_min: Optional[float] = None
    status: Optional[List[str]] = None
    search_query: Optional[str] = None

class FilterPresetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    filters: CandidateFilter
    is_shared: bool = False

class FilterPresetResponse(FilterPresetCreate):
    id: int
```

### 2.2. Endpoints

- **`POST /api/v1/candidates/search`**
  - **Description:** Searches and filters candidates.
  - **Request Body:** `CandidateFilter`
  - **Response:** A paginated list of candidates with facets.

- **`GET /api/v1/filter-options`**
  - **Description:** Retrieves available options for filters (e.g., all skills, locations).
  - **Response:** A dictionary of filter options.

- **`POST /api/v1/filter-presets`**
  - **Description:** Saves a new filter preset.
  - **Request Body:** `FilterPresetCreate`
  - **Response:** `FilterPresetResponse`

- **`GET /api/v1/filter-presets`**
  - **Description:** Retrieves all saved filter presets for the user.
  - **Response:** `List[FilterPresetResponse]`

---

## 3. SERVICE LAYER

### 3.1. Services

- **`FilterService`:** Contains the core logic for building and executing filter queries.
  - `search_candidates(filters: CandidateFilter, page: int, page_size: int)`: Builds a dynamic SQLAlchemy query based on the provided filters, executes it, and returns the results with pagination and facets.
  - `get_filter_options()`: Retrieves distinct values for skills, locations, etc., to populate the filter UI.

- **`PresetService`:** Manages the CRUD operations for filter presets.
  - `create_preset(user_id: int, preset_data: FilterPresetCreate)`
  - `get_presets_for_user(user_id: int)`

### 3.2. Query Building

The `FilterService` will dynamically construct a SQLAlchemy query. This approach is flexible and protects against SQL injection.

```python
# Example snippet from FilterService
from sqlalchemy.orm import Session

def search_candidates(db: Session, filters: CandidateFilter):
    query = db.query(Candidate)

    if filters.skills:
        # ... add skill filter logic ...

    if filters.min_experience is not None:
        query = query.filter(Candidate.total_experience_months >= filters.min_experience * 12)

    # ... other filters ...

    return query.all()
```

---

## 4. UI/UX DESIGN

- **Templates:** A new `candidate_dashboard.html` will be created or an existing one modified to include the filter panel and results view.
- **Static Files:** A `filter.js` will handle the frontend logic for applying filters, updating results via AJAX, and managing presets.

---

## 5. FILE STRUCTURE

### New Files
- `api/v1/candidates.py`: FastAPI router for candidate search and filtering.
- `services/filter_service.py`: Service for filtering logic.
- `services/preset_service.py`: Service for managing presets.
- `models/filter_models.py`: Pydantic models for this feature.
- `templates/candidate_dashboard.html`: Frontend template.
- `static/js/filter.js`: Frontend JavaScript.
- `tests/test_filters.py`: Tests for the filtering feature.

### Modified Files
- `main.py`: To include the new `candidates` API router.
- `models/schemas.py`: To add the new fields to the `Candidate` model.

---

## 6. TESTING STRATEGY

- **Unit Tests:** Test the query-building logic in `FilterService` with various combinations of filters.
- **Integration Tests:** Use `TestClient` to test the `/api/v1/candidates/search` endpoint with different filter parameters and validate the results.
- **Performance Tests:** Create a large dataset of candidates (e.g., 10,000+) and measure the response time of the search API.

---

## 7. DEPLOYMENT CONSIDERATIONS

- **Database Migration:** An Alembic migration script will be needed to add the new columns and the `filter_presets` table.
- **Data Backfill:** A script may be needed to populate the `total_experience_months` and `search_vector` for existing candidates.
