# Technical Architecture: Resume Upload & Data Extraction

**Document Status:** Draft

---

## 1. DATABASE DESIGN

### 1.1. Tables & Schema

**`candidates`**
- `id`: `SERIAL PRIMARY KEY`
- `full_name`: `VARCHAR(255) NOT NULL`
- `email`: `VARCHAR(255) UNIQUE NOT NULL`
- `phone_number`: `VARCHAR(50)`
- `linkedin_url`: `VARCHAR(500)`
- `created_at`: `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`
- `updated_at`: `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`

**`resumes`**
- `id`: `SERIAL PRIMARY KEY`
- `candidate_id`: `INTEGER REFERENCES candidates(id) ON DELETE SET NULL`
- `file_name`: `VARCHAR(255) NOT NULL`
- `file_path`: `VARCHAR(1024) NOT NULL`
- `file_hash`: `VARCHAR(64) UNIQUE NOT NULL` (SHA-256)
- `upload_status`: `VARCHAR(20) NOT NULL DEFAULT 'pending'`
- `raw_text`: `TEXT`
- `extracted_data`: `JSONB`
- `uploaded_at`: `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`

**`education`**
- `id`: `SERIAL PRIMARY KEY`
- `candidate_id`: `INTEGER REFERENCES candidates(id) ON DELETE CASCADE`
- `institution`: `VARCHAR(255)`
- `degree`: `VARCHAR(255)`
- `end_date`: `DATE`

**`work_experience`**
- `id`: `SERIAL PRIMARY KEY`
- `candidate_id`: `INTEGER REFERENCES candidates(id) ON DELETE CASCADE`
- `company`: `VARCHAR(255)`
- `job_title`: `VARCHAR(255)`
- `start_date`: `DATE`
- `end_date`: `DATE`

**`skills`**
- `id`: `SERIAL PRIMARY KEY`
- `name`: `VARCHAR(100) UNIQUE NOT NULL`

**`candidate_skills`**
- `candidate_id`: `INTEGER REFERENCES candidates(id) ON DELETE CASCADE`
- `skill_id`: `INTEGER REFERENCES skills(id) ON DELETE CASCADE`
- `PRIMARY KEY (candidate_id, skill_id)`

### 1.2. Relationships & Indexes
- **Relationships:** One-to-many from `candidates` to `resumes`, `education`, `work_experience`. Many-to-many between `candidates` and `skills` through `candidate_skills`.
- **Indexes:** Create indexes on `candidates.email`, `resumes.file_hash`, and foreign key columns.

---

## 2. API DESIGN

### 2.1. Pydantic Models

```python
# In a new file: models/resume_models.py
from pydantic import BaseModel
from typing import List, Optional

class ResumeUploadResponse(BaseModel):
    job_id: str
    file_name: str
    status: str

class CandidateCreate(BaseModel):
    full_name: str
    email: str
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None

class CandidateResponse(CandidateCreate):
    id: int
```

### 2.2. Endpoints

- **`POST /api/v1/resumes/upload`**
  - **Description:** Uploads a single resume.
  - **Request Body:** `file: UploadFile`
  - **Response:** `ResumeUploadResponse`

- **`POST /api/v1/resumes/upload-batch`**
  - **Description:** Uploads a batch of resumes.
  - **Request Body:** `files: List[UploadFile]`
  - **Response:** `List[ResumeUploadResponse]`

- **`GET /api/v1/jobs/{job_id}`**
  - **Description:** Checks the status of a processing job.
  - **Response:** `{"job_id": str, "status": str, "result": Optional[dict]}`

---

## 3. SERVICE LAYER

### 3.1. Services

- **`ResumeService`:** Handles the business logic for uploading and processing resumes.
  - `upload_resume(file: UploadFile)`: Saves the file and creates a processing job.
  - `process_resume(job_id: str)`: The background task that performs extraction and duplicate checking.
- **`CandidateService`:** Manages candidate data.
  - `find_duplicate(email: str, phone: str)`: Checks for existing candidates.
  - `create_candidate(data: CandidateCreate)`: Creates a new candidate profile.

### 3.2. Business Logic
1.  **Upload:** The API endpoint receives the file, saves it to a temporary location (e.g., `uploads/`), and creates a `Resume` record in the database with 'pending' status. It then triggers a background task (Celery) with the resume ID.
2.  **Processing (Background Task):**
    - The worker picks up the job.
    - It updates the resume status to 'processing'.
    - It extracts text using `PyMuPDF` or `python-docx`.
    - It uses `spaCy` to parse the text and extract entities.
    - It checks for duplicates using the `CandidateService`.
    - If no duplicates, it creates a new candidate and associated records (education, experience, etc.).
    - It updates the resume status to 'completed' or 'failed'.

---

## 4. UI/UX DESIGN

- **Templates:** A new template `resume_upload.html` will be created.
- **Static Files:** New JavaScript file `resume_upload.js` to handle AJAX uploads and status polling.
- **User Flow:** The user will see an upload button. Upon clicking, they can select files. The upload will happen in the background, and the UI will show a list of recently uploaded resumes with their processing status.

---

## 5. INTEGRATION POINTS

- This feature will be largely self-contained but will write to the `candidates` table, which may be used by other parts of the application.
- The existing `main.py` will be modified to include the new router for resume-related endpoints.

---

## 6. FILE STRUCTURE

### New Files
- `api/v1/resumes.py`: FastAPI router for resume endpoints.
- `services/resume_service.py`: Service for resume processing logic.
- `services/candidate_service.py`: Service for candidate data management.
- `models/resume_models.py`: Pydantic models for resume feature.
- `templates/resume_upload.html`: Frontend template.
- `static/js/resume_upload.js`: Frontend JavaScript.
- `tests/test_resumes.py`: Tests for the new feature.

### Modified Files
- `main.py`: To include the new API router.
- `models/schemas.py`: To add any new shared schemas (if any).
- `requirements.txt`: To add new dependencies like `celery` and `redis` if not already present.

---

## 7. TESTING STRATEGY

- **Unit Tests:** In `tests/test_resumes.py`, we will mock the file system and database to test the `ResumeService` methods in isolation.
- **Integration Tests:** We will use FastAPI's `TestClient` to make real HTTP requests to the upload endpoints and verify that the entire flow works as expected, including background task execution.
- **Manual Testing:** A checklist will be created to test the UI flow, including error states and duplicate handling.

---

## 8. DEPLOYMENT CONSIDERATIONS

- **Environment Variables:**
  - `CELERY_BROKER_URL`: URL for the Redis instance.
  - `CELERY_RESULT_BACKEND`: URL for the Redis instance.
- **Migrations:** A database migration script (e.g., using Alembic) will be required to create the new tables.
- **Infrastructure:** A Celery worker and a Redis instance will need to be deployed alongside the FastAPI application.
