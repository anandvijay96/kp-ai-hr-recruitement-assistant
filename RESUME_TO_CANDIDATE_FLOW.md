# Resume Upload to Candidate Creation Flow

## Overview
This document describes the automated flow from resume upload to candidate creation in the HR Recruitment System.

## Flow Description

### 1. Resume Upload (`/resumes/upload-new`)
- User uploads resume files (PDF, DOCX, TXT)
- Maximum file size: 10MB
- Bulk upload: Up to 50 files

### 2. Automatic Processing
When a resume is uploaded with `auto_parse=True` (default):

1. **File Validation**
   - File type check
   - File size validation
   - Duplicate detection (by file hash)

2. **Resume Parsing**
   - Extract text content
   - Parse structured data:
     - Personal information (name, email, phone, location, LinkedIn)
     - Education history
     - Work experience
     - Skills
     - Certifications

3. **Duplicate Detection**
   - Check for existing candidates with:
     - Same email
     - Same phone number
     - Similar name

4. **Candidate Creation**
   - If no duplicates found:
     - Create candidate record
     - Link education, experience, skills, certifications
     - Link resume to candidate
     - Set status to "new"
   - If duplicates found:
     - Return duplicate candidates for user review
     - User can choose: skip, merge, or force create

### 3. Redirect to Candidates List
After successful upload:
- User is automatically redirected to `/candidates`
- Newly created candidates appear in the list
- Status shows as "new"

## API Endpoints

### Upload Resume
```
POST /api/resumes/upload
```

**Parameters:**
- `file`: Resume file (required)
- `candidate_name`: Optional override
- `candidate_email`: Optional override
- `candidate_phone`: Optional override
- `auto_parse`: Boolean (default: true)

**Response:**
```json
{
  "success": true,
  "message": "Resume uploaded successfully",
  "data": {
    "resume_id": "uuid",
    "candidate_id": "uuid",
    "candidate_created": true
  }
}
```

### List Candidates
```
GET /api/candidates
```

**Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)
- `search`: Search term
- `status`: Filter by status

## Authentication

All API endpoints require authentication via JWT token:
```
Authorization: Bearer <access_token>
```

### Token Expiration Handling
- Token stored in `localStorage.access_token`
- On 401 response:
  - Clear token from localStorage
  - Redirect to `/login`
  - Show "Session expired" message

## User Interface

### Upload Page (`/resumes/upload-new`)
- Drag & drop interface
- File validation feedback
- Upload progress tracking
- Success message with redirect

### Candidates Page (`/candidates`)
- Paginated list of candidates
- Search and filter capabilities
- Quick actions: View, Edit
- Link to upload more resumes

## Error Handling

### Upload Errors
- **File too large**: "File size exceeds 10MB limit"
- **Invalid format**: "Invalid file format. Allowed: PDF, DOCX, TXT"
- **Duplicate file**: Returns existing resume info
- **Token expired**: Redirect to login

### Parsing Errors
- Resume uploaded but parsing failed
- User can manually parse later via `/api/resumes/{id}/parse`

### Duplicate Candidates
- Returns list of potential duplicates
- User resolves via `/api/resumes/{id}/resolve-duplicate`
- Options: skip, merge, force_create

## Database Schema

### Resume Table
- `id`: UUID
- `file_path`: Storage path
- `file_hash`: For duplicate detection
- `candidate_id`: Link to candidate
- `processing_status`: pending, completed, failed
- `uploaded_by`: User ID

### Candidate Table
- `id`: UUID
- `full_name`: String
- `email`: String (unique)
- `phone`: String
- `status`: new, screened, interviewed, offered, hired, rejected
- `source`: upload, manual, import

## Testing

### Manual Testing Steps
1. Login to the system
2. Navigate to `/resumes/upload-new`
3. Upload a resume file
4. Wait for processing
5. Click "Close" on success modal
6. Verify redirect to `/candidates`
7. Verify new candidate appears in list

### Expected Behavior
- Resume uploads successfully
- Candidate is auto-created
- User redirected to candidates page
- New candidate visible with status "new"

## Troubleshooting

### Candidate Not Appearing
1. Check if duplicates were detected
2. Verify `auto_parse` was true
3. Check resume processing status
4. Review server logs for parsing errors

### Token Expired Error
1. Login again at `/login`
2. Token expires after configured duration
3. Refresh page to trigger redirect

### Upload Fails
1. Check file size and format
2. Verify authentication token
3. Check server logs
4. Ensure database is accessible

## Recent Changes

### 2025-10-06
- ✅ Updated upload page to redirect to `/candidates` after success
- ✅ Added token expiration handling in upload page
- ✅ Added token expiration handling in candidates page
- ✅ Added success message indicating candidates were created
- ✅ Added "View Resumes" button to candidates page header

## Related Files

- `api/resumes.py` - Resume upload endpoints
- `api/candidates.py` - Candidate management endpoints
- `services/candidate_service.py` - Candidate creation logic
- `services/resume_parser_service.py` - Resume parsing
- `services/duplicate_detection_service.py` - Duplicate detection
- `templates/resumes/upload_new.html` - Upload UI
- `templates/candidates/list.html` - Candidates list UI
