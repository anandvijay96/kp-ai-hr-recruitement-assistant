# PRD: Comprehensive Resume Upload & Data Extraction

**Feature ID:** 03
**Feature Name:** Comprehensive Resume Upload & Data Extraction
**Priority:** P0 (Critical)
**Status:** Drafting

---

## 1. OVERVIEW

### 1.1. Brief Description
This feature enables HR personnel to upload candidate resumes (single or in bulk) into the recruitment application. The system will automatically parse the resumes, extract key information, and populate the candidate database, significantly reducing manual data entry.

### 1.2. Problem Statement
Recruiters spend a significant amount of time manually entering data from resumes into the applicant tracking system. This process is time-consuming, error-prone, and inefficient, especially when dealing with a high volume of applications. This feature aims to automate the data entry process, improve data accuracy, and streamline the initial stages of the recruitment pipeline.

### 1.3. Target Users
- **Recruiters:** Primary users who will upload resumes and manage candidate data.
- **Hiring Managers:** Secondary users who will review the extracted candidate information.
- **System Administrators:** Users responsible for system configuration and maintenance.

---

## 2. USER STORIES

- **US-3.1:** As a recruiter, I want to upload a single resume file (PDF, DOC, DOCX) so that I can quickly add a new candidate to the system.
- **US-3.2:** As a recruiter, I want to upload a batch of up to 50 resumes simultaneously via a drag-and-drop interface so that I can efficiently process candidates from a job fair or online sourcing.
- **US-3.3:** As a system, I want to automatically extract key information (personal details, work experience, education, skills) from the uploaded resumes so that the candidate profile is created without manual data entry.
- **US-3.4:** As a recruiter, I want to be notified of potential duplicate candidates based on email, phone number, or name, so that I can avoid creating redundant profiles and maintain a clean database.
- **US-3.5:** As a recruiter, I want to review and edit the extracted information before saving the candidate profile to ensure data accuracy.

---

## 3. ACCEPTANCE CRITERIA

### For US-3.1: Single Resume Upload
- The system must accept files with `.pdf`, `.doc`, and `.docx` extensions.
- A file size limit of 10MB must be enforced.
- An error message must be displayed for unsupported file types or sizes.
- A success message must be displayed upon successful upload and processing.

### For US-3.2: Bulk Resume Upload
- The UI must provide a drag-and-drop area for files.
- The system must accept up to 50 files in a single batch.
- The system must display the progress of each upload and the overall batch progress.
- A summary report of successful and failed uploads must be provided after the batch is processed.

### For US-3.3: Data Extraction
- The system must extract the following fields with at least 95% accuracy:
  - Full Name
  - Email Address
  - Phone Number
  - LinkedIn Profile URL
  - Education History (Institution, Degree, Graduation Date)
  - Work Experience (Company, Job Title, Dates of Employment)
  - Skills

### For US-3.4: Duplicate Detection
- The system must check for duplicates based on an exact match of the email address.
- The system must check for duplicates based on a normalized phone number.
- The system must suggest potential duplicates based on a fuzzy match of the candidate's name.
- When a duplicate is detected, the recruiter must be given the option to merge the new information, discard the new resume, or create a new profile anyway.

### For US-3.5: Review and Edit
- After data extraction, the system must present the extracted information to the recruiter in an editable form.
- The recruiter must be able to correct any inaccuracies in the extracted data.
- The recruiter must be able to save the corrected data to the candidate's profile.

---

## 4. TECHNICAL DESIGN

### 4.1. Database Schema

**`candidates` table**
- `id` (PK, SERIAL)
- `full_name` (VARCHAR)
- `email` (VARCHAR, UNIQUE)
- `phone_number` (VARCHAR)
- `linkedin_url` (VARCHAR)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**`resumes` table**
- `id` (PK, SERIAL)
- `candidate_id` (FK to `candidates.id`)
- `file_name` (VARCHAR)
- `file_path` (VARCHAR)
- `file_hash` (VARCHAR, UNIQUE) - To prevent re-processing the same file.
- `upload_status` (ENUM: 'pending', 'processing', 'completed', 'failed')
- `raw_text` (TEXT)
- `extracted_data` (JSONB)
- `uploaded_at` (TIMESTAMP)

**`education` table**
- `id` (PK, SERIAL)
- `candidate_id` (FK to `candidates.id`)
- `institution` (VARCHAR)
- `degree` (VARCHAR)
- `end_date` (DATE)

**`work_experience` table**
- `id` (PK, SERIAL)
- `candidate_id` (FK to `candidates.id`)
- `company` (VARCHAR)
- `job_title` (VARCHAR)
- `start_date` (DATE)
- `end_date` (DATE)

**`skills` table**
- `id` (PK, SERIAL)
- `name` (VARCHAR, UNIQUE)

**`candidate_skills` table (Many-to-Many)**
- `candidate_id` (FK to `candidates.id`)
- `skill_id` (FK to `skills.id`)

### 4.2. API Endpoints

- `POST /api/resumes/upload`: For single resume uploads. Accepts multipart/form-data.
- `POST /api/resumes/upload-batch`: For bulk resume uploads. Accepts a list of files.
- `GET /api/resumes/{resume_id}/status`: To check the processing status of a specific resume.
- `GET /api/candidates/{candidate_id}`: To retrieve a candidate's profile.
- `PUT /api/candidates/{candidate_id}`: To update a candidate's profile after review.

### 4.3. UI Components and User Flow
1.  **Upload Component:** A section on the dashboard with a file input and a drag-and-drop zone.
2.  **Progress Indicator:** A modal or section that shows the status of ongoing uploads.
3.  **Review Form:** A form pre-filled with extracted data, allowing for edits.
4.  **User Flow:**
    - User drags/selects resume(s).
    - Frontend uploads file(s) to the API.
    - API returns a job ID and saves the file.
    - A background worker processes the resume (extraction, duplicate check).
    - Frontend polls for status.
    - Once processed, the user is notified and can review the data.

### 4.4. Integration Points
- This feature will integrate with the existing `candidates` module.
- It will utilize the existing user authentication service to associate uploads with a recruiter.

---

## 5. DEPENDENCIES

### 5.1. External Libraries
- `python-docx`: To parse `.docx` files.
- `PyMuPDF`: To parse `.pdf` files.
- `spaCy`: For Natural Language Processing (NLP) to extract entities.
- `Celery`: For background task processing.
- `Redis`: As a message broker for Celery.

### 5.2. Internal Modules
- `models`: Will need updates to `schemas.py` for new data structures.
- `services`: New services for resume parsing and processing will be created.
- `api`: New endpoints will be added.

---

## 6. TESTING PLAN

### 6.1. Unit Tests
- Test file parsing for different resume layouts and formats.
- Test data extraction logic for each field.
- Test duplicate detection algorithms.

### 6.2. Integration Tests
- Test the full upload-to-save flow for a single resume.
- Test the batch upload process and status tracking.
- Test the API endpoints with various valid and invalid inputs.

### 6.3. Manual Testing Scenarios
- Upload a corrupted/password-protected file.
- Upload a file larger than the size limit.
- Test the duplicate resolution flow (merge, skip, create new).
- Test editing and saving extracted data.

### 6.4. Edge Cases
- Resumes with unconventional formatting.
- Resumes in a language other than English.
- Extremely large resume files.

---

## 7. IMPLEMENTATION PLAN

### Phase 1: Core Backend (1 week)
- **Tasks:**
  - Update database schema and create migrations.
  - Implement single resume upload endpoint.
  - Set up background worker with Celery.
  - Implement basic text extraction for PDF and DOCX.
- **Effort:** High

### Phase 2: Data Extraction & Duplicate Detection (1 week)
- **Tasks:**
  - Implement NLP-based data extraction for all required fields.
  - Implement duplicate detection logic.
  - Add status tracking for background jobs.
- **Effort:** High
- **Risks:** Data extraction accuracy may vary. Mitigation: Use a robust NLP model and have a manual review step.

### Phase 3: Frontend and Finalization (1 week)
- **Tasks:**
  - Develop the UI for uploading, progress tracking, and reviewing.
  - Integrate frontend with the backend APIs.
  - Conduct end-to-end testing.
- **Effort:** Medium
- **Risks:** UI complexity. Mitigation: Start with a simple interface and iterate.

---

## 8. SUCCESS METRICS

- **Time to add a new candidate:** Reduction by at least 80%.
- **Data entry error rate:** Decrease in manual correction rates by 50%.
- **User adoption:** 90% of recruiters using the feature within the first month.
- **System performance:** Average processing time per resume under 30 seconds.
