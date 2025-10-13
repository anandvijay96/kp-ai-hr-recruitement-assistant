# Feature 2: Resume Upload & Data Extraction - Implementation Guide

## Overview

This feature enhances the HR recruitment system with advanced resume parsing, candidate management, and duplicate detection capabilities.

## Features Implemented

### ✅ 1. Database Schema
- **Candidates Table**: Stores candidate personal information
- **Education Table**: Academic qualifications
- **Work Experience Table**: Professional history
- **Skills Table**: Master skills list with candidate associations
- **Certifications Table**: Professional certifications
- **Duplicate Checks Table**: Audit trail for duplicate detection

### ✅ 2. Services Layer
- **CandidateService**: Complete CRUD operations for candidates
- **DuplicateDetectionService**: Multi-method duplicate detection (email, phone, name similarity)
- **Enhanced ResumeParserService**: Structured data extraction from resumes

### ✅ 3. API Endpoints

#### Candidate Management
- `GET /api/candidates` - List candidates with pagination and filters
- `GET /api/candidates/{id}` - Get candidate details
- `PUT /api/candidates/{id}` - Update candidate
- `DELETE /api/candidates/{id}` - Delete (archive) candidate
- `POST /api/candidates/{source_id}/merge/{target_id}` - Merge candidates
- `GET /api/candidates/stats/overview` - Get statistics

#### Resume Processing
- `POST /api/resumes/{id}/parse` - Parse resume and create candidate
- `POST /api/resumes/check-duplicate-candidate` - Check for duplicates
- `POST /api/resumes/{id}/resolve-duplicate` - Resolve duplicate situation

### ✅ 4. User Interface
- **Candidates List Page**: Browse and search candidates
- **Candidate Detail Page**: View complete candidate profile

### ✅ 5. Testing
- Comprehensive unit tests for CandidateService
- Integration tests for DuplicateDetectionService
- Test fixtures and sample data

## Installation & Setup

### 1. Install Dependencies

```bash
# Install required packages
pip install fuzzywuzzy python-Levenshtein

# Or using uv
uv pip install fuzzywuzzy python-Levenshtein
```

### 2. Run Database Migration

```bash
# Run the migration script
python migrations/002_add_candidate_tables.py

# Or rollback if needed
python migrations/002_add_candidate_tables.py downgrade
```

### 3. Verify Installation

```bash
# Run tests
pytest tests/test_candidate_service.py -v
pytest tests/test_duplicate_detection_service.py -v
```

## Usage Guide

### Uploading and Processing Resumes

1. **Upload Resume**
   ```bash
   POST /api/resumes/upload
   Content-Type: multipart/form-data
   
   file: resume.pdf
   ```

2. **Parse Resume and Create Candidate**
   ```bash
   POST /api/resumes/{resume_id}/parse?check_duplicates=true
   ```

3. **Handle Duplicates** (if found)
   ```bash
   POST /api/resumes/{resume_id}/resolve-duplicate
   
   {
     "action": "merge",  // or "skip" or "force_create"
     "matched_candidate_id": "candidate-uuid"
   }
   ```

### Managing Candidates

1. **List Candidates**
   ```bash
   GET /api/candidates?page=1&limit=20&search=john&status=new
   ```

2. **View Candidate Details**
   ```bash
   GET /api/candidates/{candidate_id}
   ```

3. **Update Candidate**
   ```bash
   PUT /api/candidates/{candidate_id}
   
   {
     "full_name": "John Smith",
     "status": "interviewed",
     "location": "New York, NY"
   }
   ```

4. **Merge Candidates**
   ```bash
   POST /api/candidates/{source_id}/merge/{target_id}
   ```

## Duplicate Detection

The system uses multiple methods to detect duplicates:

### 1. Email Match (Exact)
- **Priority**: Highest
- **Method**: Normalized email comparison
- **Confidence**: 100%

### 2. Phone Match (Normalized)
- **Priority**: High
- **Method**: Last 10 digits comparison
- **Confidence**: 100%

### 3. Name Similarity (Fuzzy)
- **Priority**: Medium
- **Method**: Levenshtein distance
- **Threshold**: 85% similarity
- **Confidence**: Variable

## Data Structure

### Parsed Resume Data
```json
{
  "personal_info": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "linkedin_url": "linkedin.com/in/johndoe",
    "location": "San Francisco, CA"
  },
  "education": [
    {
      "degree": "Bachelor of Science",
      "field": "Computer Science",
      "institution": "Stanford University",
      "start_date": "2015-09",
      "end_date": "2019-06",
      "gpa": "3.8"
    }
  ],
  "experience": [
    {
      "company": "Google",
      "title": "Senior Software Engineer",
      "start_date": "2021-03",
      "end_date": "Present",
      "duration_months": 42
    }
  ],
  "skills": [
    {
      "name": "Python",
      "category": "technical",
      "proficiency": "expert"
    }
  ],
  "certifications": []
}
```

## Configuration

### Environment Variables
```bash
# No additional environment variables required
# Uses existing database and authentication
```

## Testing

### Run All Tests
```bash
# Run all feature tests
pytest tests/test_candidate_service.py tests/test_duplicate_detection_service.py -v

# Run with coverage
pytest --cov=services --cov=api tests/ -v
```

### Manual Testing Checklist

- [ ] Upload single PDF resume
- [ ] Upload single DOCX resume
- [ ] Parse resume and create candidate
- [ ] Detect duplicate by email
- [ ] Detect duplicate by phone
- [ ] Resolve duplicate (skip)
- [ ] Resolve duplicate (merge)
- [ ] Resolve duplicate (force create)
- [ ] View candidate list
- [ ] Search candidates
- [ ] Filter candidates by status
- [ ] View candidate details
- [ ] Update candidate information
- [ ] Merge two candidates
- [ ] Delete candidate

## Troubleshooting

### Issue: fuzzywuzzy not working
**Solution**: Install python-Levenshtein for better performance
```bash
pip install python-Levenshtein
```

### Issue: Migration fails
**Solution**: Check if tables already exist
```bash
# View existing tables
sqlite3 hr_recruitment.db ".tables"

# If tables exist, migration will skip them
```

### Issue: Duplicate detection not working
**Solution**: Verify data normalization
```python
# Email should be lowercase
# Phone should be digits only (last 10)
```

## Performance Considerations

- **Indexing**: All foreign keys and search fields are indexed
- **Pagination**: Default 20 items per page, max 100
- **Caching**: Consider adding Redis cache for duplicate checks
- **Background Jobs**: Large batch operations should use Celery

## Future Enhancements

1. **Background Processing**: Integrate Celery for async parsing
2. **Advanced Matching**: ML-based content similarity
3. **Bulk Operations**: Batch candidate updates
4. **Export**: CSV/Excel export of candidates
5. **Analytics**: Candidate pipeline analytics

## API Documentation

Full API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Support

For issues or questions:
1. Check the logs: `logs/app.log`
2. Review test cases for examples
3. Consult the technical implementation document

## Version History

- **v1.0.0** (2025-10-06): Initial implementation
  - Candidate management
  - Duplicate detection
  - Resume parsing integration
  - UI templates
  - Comprehensive tests
