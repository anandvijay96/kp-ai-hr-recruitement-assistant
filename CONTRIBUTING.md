# 🚀 Contributing to AI HR Assistant - Beginner's Guide

Welcome! This guide will help you start contributing to the AI HR Assistant project. Follow these steps carefully.

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Project Setup](#project-setup)
3. [Git Workflow](#git-workflow)
4. [Creating a Feature Branch](#creating-a-feature-branch)
5. [Making Changes](#making-changes)
6. [Testing Your Changes](#testing-your-changes)
7. [Committing and Pushing](#committing-and-pushing)
8. [Creating a Pull Request](#creating-a-pull-request)
9. [Code Review Process](#code-review-process)
10. [Features to Implement](#features-to-implement)
11. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

Before you start, ensure you have:
- ✅ Git installed on your machine
- ✅ Python 3.10+ installed
- ✅ UV package manager installed (or pip)
- ✅ Project cloned and running locally
- ✅ WSL or Linux environment (recommended)
- ✅ Code editor (VS Code or Cursor or Windsurf recommended)

### Verify Your Setup

```bash
# Check Git
git --version

# Check Python
python --version

# Check UV
uv --version

# Navigate to project
cd ai-hr-assistant

# Verify you're on main branch
git branch
# Should show: * main
```

---

## 2. Project Setup

If you haven't set up the project yet:

```bash
# Clone the repository
git clone https://github.com/anandvijay96/kp-ai-hr-recruitement-assistant.git
cd kp-ai-hr-recruitement-assistant

# Install dependencies
uv sync

# Run the application
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Open browser
# Visit: http://localhost:8000
```

---

## 3. Git Workflow

We follow a **feature branch workflow**:

```
main (production-ready code)
  ↓
feature/your-feature-name (your work)
  ↓
Pull Request → Code Review → Merge to main
```

### Important Rules:
- ❌ **NEVER commit directly to `main`**
- ✅ Always create a feature branch
- ✅ One feature = One branch
- ✅ Keep branches small and focused
- ✅ Pull latest changes before starting

---

## 4. Creating a Feature Branch

### Step 1: Ensure You're on Main Branch

```bash
# Switch to main branch
git checkout main

# Pull latest changes
git pull origin main
```

### Step 2: Create a New Feature Branch

**Branch Naming Convention:**
```
feature/short-description
bugfix/issue-description
enhancement/improvement-name
```

**Examples:**
```bash
# For adding results history page
git checkout -b feature/results-history-page

# For fixing upload bug
git checkout -b bugfix/file-upload-error

# For improving UI
git checkout -b enhancement/better-loading-states
```

**Create Your Branch:**
```bash
# Replace 'your-feature-name' with actual feature
git checkout -b feature/your-feature-name

# Verify you're on the new branch
git branch
# Should show: * feature/your-feature-name
```

---

## 5. Making Changes

### Project Structure

```
ai-hr-assistant/
├── main.py                 # Main FastAPI application
├── core/
│   ├── config.py          # Configuration settings
│   └── cache.py           # Caching logic
├── models/
│   └── schemas.py         # Pydantic models
├── services/
│   ├── document_processor.py    # PDF/DOCX processing
│   ├── resume_analyzer.py       # Authenticity analysis
│   ├── jd_matcher.py           # JD matching
│   └── result_storage.py       # Result persistence
├── templates/
│   ├── index.html         # Home page
│   └── upload.html        # Upload page
├── tests/
│   └── test_*.py          # Test files
└── requirements.txt       # Dependencies
```

### Making Code Changes

1. **Open your code editor**
```bash
code .  # If using VS Code
```

2. **Make your changes**
   - Edit files as needed
   - Follow existing code style
   - Add comments for complex logic

3. **Test as you go**
```bash
# Run the app
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Test in browser
# Visit: http://localhost:8000
```

---

## 6. Testing Your Changes

### Manual Testing

1. **Start the application**
```bash
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

2. **Test all affected features**
   - Upload a resume
   - Check if your changes work
   - Test edge cases
   - Verify nothing broke

### Automated Testing

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test file
uv run python -m pytest tests/test_main.py -v

# Run with coverage
uv run python -m pytest tests/ --cov=. --cov-report=html
```

### Checklist Before Committing:
- [ ] Code runs without errors
- [ ] All tests pass
- [ ] Manual testing completed
- [ ] No console errors
- [ ] Code follows project style
- [ ] Comments added where needed

---

## 7. Committing and Pushing

### Step 1: Check What Changed

```bash
# See modified files
git status

# See actual changes
git diff
```

### Step 2: Stage Your Changes

```bash
# Stage specific files
git add path/to/file1.py path/to/file2.py

# Or stage all changes (be careful!)
git add .

# Verify what's staged
git status
```

### Step 3: Commit Your Changes

**Commit Message Format:**
```
<type>: <short description>

<optional longer description>
<optional issue reference>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```bash
# Good commit messages
git commit -m "feat: add results history page with pagination"
git commit -m "fix: resolve file upload validation error"
git commit -m "docs: update README with new features"

# Bad commit messages (avoid these)
git commit -m "changes"
git commit -m "fix"
git commit -m "updated files"
```

### Step 4: Push to GitHub

```bash
# First time pushing this branch
git push -u origin feature/your-feature-name

# Subsequent pushes
git push
```

---

## 8. Creating a Pull Request

### Step 1: Go to GitHub

1. Visit: https://github.com/anandvijay96/kp-ai-hr-recruitement-assistant
2. You'll see a banner: "Compare & pull request"
3. Click the button

### Step 2: Fill PR Details

**Title:**
```
feat: Add results history page
```

**Description Template:**
```markdown
## What does this PR do?
Brief description of changes

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Code refactoring

## How to Test
1. Step 1
2. Step 2
3. Expected result

## Screenshots (if applicable)
[Add screenshots]

## Checklist
- [ ] Code runs locally
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No console errors
```

### Step 3: Request Review

- Assign reviewer (your senior)
- Add labels if available
- Click "Create Pull Request"

---

## 9. Code Review Process

### What Happens Next:

1. **Reviewer Gets Notified**
   - Your senior will review your code
   - They may leave comments or request changes

2. **Address Feedback**
   ```bash
   # Make requested changes
   # Then commit and push again
   git add .
   git commit -m "fix: address review comments"
   git push
   ```

3. **Approval & Merge**
   - Once approved, your code will be merged to `main`
   - Your branch will be deleted (automatically or manually)

### After Merge:

```bash
# Switch back to main
git checkout main

# Pull latest changes (includes your merged code)
git pull origin main

# Delete your local feature branch
git branch -d feature/your-feature-name
```

---

## 10. Features to Implement

Here are the features planned for the full application. Each feature should be broken down into user stories before implementation.

---

## 🎯 Feature 1: User Authentication & Management

**Branch:** `feature/user-authentication`

**Epic:** User Management System

**User Stories:**

1. **User Registration**
   - As a new user, I want to register with my details
   - Fields: Full name, email, mobile, password, confirm password
   - Email verification with code
   - Role selection (Admin, Recruiter)
   - Department/Team assignment

2. **User Login**
   - As a user, I want to log in with email/password
   - Session management
   - Remember me option
   - Login attempt tracking

3. **Password Management**
   - As a user, I want to reset my password if forgotten
   - Email-based password reset
   - Password strength requirements
   - Password change functionality

**Technical Requirements:**
- Authentication library (JWT or session-based)
- Email service integration (SendGrid, AWS SES)
- Password hashing (bcrypt)
- Database tables: users, roles, sessions

**Files to Create:**
- `models/user.py` - User model
- `services/auth_service.py` - Authentication logic
- `services/email_service.py` - Email sending
- `api/auth.py` - Auth endpoints
- `templates/login.html`, `register.html`, `forgot_password.html`
- `tests/test_auth.py`

---

## 🎯 Feature 2: Enhanced Resume Upload & Processing

**Branch:** `feature/resume-upload-enhancement`

**Epic:** Resume Management

**User Stories:**

1. **Bulk Resume Upload**
   - As a recruiter, I want to upload multiple resumes at once
   - Drag-and-drop interface
   - Progress tracking for batch uploads
   - Error handling per file

2. **Resume Data Extraction**
   - Extract: Name, email, LinkedIn, phone, education, certifications, work experience
   - Store structured data in database
   - Handle various resume formats

3. **Duplicate Detection**
   - As a recruiter, I want to be notified of duplicate resumes
   - Check by email, phone, or content similarity
   - Option to merge or skip duplicates

**Technical Requirements:**
- Enhanced NLP for data extraction
- Database schema for resume data
- Duplicate detection algorithm
- Background job processing (Celery/Redis)

**Files to Create:**
- `models/resume.py`, `models/candidate.py`
- `services/resume_parser.py` - Enhanced parsing
- `services/duplicate_detector.py`
- `api/resume.py` - Resume endpoints
- `templates/bulk_upload.html`
- `tests/test_resume_parser.py`

---

## 🎯 Feature 3: Advanced Resume Filtering

**Branch:** `feature/resume-filtering`

**Epic:** Resume Search & Discovery

**User Stories:**

1. **Basic Filters**
   - Filter by skills/keywords
   - Filter by years of experience
   - Filter by education qualification
   - Filter by location & availability

2. **Advanced Filters**
   - Filter by resume rating
   - Filter by status (New, Screened, Interviewed, Rejected)
   - Boolean search (AND, OR, NOT)
   - Save filter presets

**Technical Requirements:**
- Full-text search (Elasticsearch or PostgreSQL FTS)
- Complex query builder
- Filter persistence
- Export filtered results

**Files to Create:**
- `services/search_service.py`
- `api/search.py`
- `templates/search.html`
- `tests/test_search.py`

---

## 🎯 Feature 4: Candidate Tracking System

**Branch:** `feature/candidate-tracking`

**Epic:** Recruitment Pipeline

**User Stories:**

1. **Status Tracking**
   - Track: Received → Shortlisted → Interviewed → Hired/Rejected
   - Visual pipeline/kanban board
   - Drag-and-drop status updates

2. **Interview Scheduling**
   - Integration with Google Calendar/Outlook
   - Send interview invites
   - Track confirmations/declines

3. **Activity Timeline**
   - View complete candidate journey
   - All interactions logged
   - Recruiter comments/feedback

4. **Notifications**
   - Pending actions alerts
   - Interview reminders
   - Status change notifications

**Technical Requirements:**
- Calendar API integration
- Notification system (email + in-app)
- Activity logging
- WebSocket for real-time updates

**Files to Create:**
- `models/candidate_status.py`, `models/interview.py`
- `services/calendar_service.py`
- `services/notification_service.py`
- `api/tracking.py`
- `templates/pipeline.html`, `timeline.html`
- `tests/test_tracking.py`

---

## 🎯 Feature 5: Manual Resume Rating System

**Branch:** `feature/resume-rating`

**Epic:** Resume Evaluation

**User Stories:**

1. **Recruiter Rating**
   - Rate resumes 1-5 stars
   - Add comments/justification
   - Rating per interview round

2. **Rating Management**
   - Compare ratings across recruiters
   - View rating history
   - Export ratings for reports

**Technical Requirements:**
- Rating storage with audit trail
- Multi-recruiter rating aggregation
- Rating analytics

**Files to Create:**
- `models/rating.py`
- `services/rating_service.py`
- `api/rating.py`
- `templates/rate_resume.html`
- `tests/test_rating.py`

---

## 🎯 Feature 6: Job Creation & Management

**Branch:** `feature/job-management`

**Epic:** Job Posting System

**User Stories:**

1. **Create Job Posting**
   - Job title, description, requirements
   - Skill tags and qualifications
   - Number of openings
   - Location & work type (onsite/remote/hybrid)
   - Application deadline
   - Attach JD document

2. **Job Lifecycle**
   - Dashboard of active/inactive jobs
   - Track: Open → In Progress → Closed
   - Candidate pipeline per job
   - Assign multiple recruiters

3. **Job Distribution**
   - Post to external portals (LinkedIn, Naukri, Indeed)
   - Track applications from each source
   - Job performance metrics

**Technical Requirements:**
- Job posting APIs integration
- Job-candidate relationship management
- Analytics dashboard

**Files to Create:**
- `models/job.py`, `models/job_application.py`
- `services/job_service.py`
- `services/job_posting_service.py`
- `api/jobs.py`
- `templates/create_job.html`, `job_dashboard.html`
- `tests/test_jobs.py`

---

## 🎯 Feature 7: AI-Powered Resume Matching

**Branch:** `feature/ai-resume-matching`

**Epic:** Intelligent Matching

**User Stories:**

1. **Automatic Matching**
   - AI auto-match resumes against job requirements
   - Match percentage score
   - Highlight matched vs missing skills
   - Rank by relevancy

2. **Match Insights**
   - Explainability of match score
   - Automatic shortlist suggestions
   - Real-time matching on new uploads

**Technical Requirements:**
- Enhanced matching algorithm (already partially implemented)
- Background job for batch matching
- Match score explanation logic

**Files to Create:**
- `services/ai_matcher.py` (enhance existing)
- `services/match_explainer.py`
- `api/matching.py`
- `templates/match_results.html`
- `tests/test_ai_matching.py`

---

## 🎯 Feature 8: Resume Match Rating & Ranking

**Branch:** `feature/resume-ranking`

**Epic:** Candidate Prioritization

**User Stories:**

1. **Multi-Criteria Scoring**
   - Score based on: skills, experience, education
   - Weighted scoring system
   - Configurable weights per job

2. **Ranking & Recommendations**
   - Sort candidates by rating
   - Highlight top 5 recommended
   - Export ranked list
   - Display in candidate list view

**Technical Requirements:**
- Scoring algorithm
- Ranking system
- Export functionality

**Files to Create:**
- `services/ranking_service.py`
- `api/ranking.py`
- `templates/ranked_candidates.html`
- `tests/test_ranking.py`

---

## 🎯 Feature 9: Advanced User Management

**Branch:** `feature/user-management-admin`

**Epic:** Admin Panel

**User Stories:**

1. **User Administration**
   - Create, edit, delete user accounts
   - Activate/deactivate accounts
   - Reset passwords
   - Enforce password policies

2. **Role-Based Access Control (RBAC)**
   - Define roles and permissions
   - Assign permissions at module level
   - Role hierarchy

3. **Activity Tracking**
   - Track user activity logs
   - Assign recruiter to clients/jobs
   - Audit trail

**Technical Requirements:**
- RBAC implementation
- Activity logging middleware
- Admin dashboard

**Files to Create:**
- `models/role.py`, `models/permission.py`
- `services/rbac_service.py`
- `middleware/auth_middleware.py`
- `api/admin.py`
- `templates/admin/users.html`
- `tests/test_rbac.py`

---

## 📊 Implementation Priority

**Phase 1 (Foundation):**
1. User Authentication & Management
2. Enhanced Resume Upload & Processing

**Phase 2 (Core Features):**
3. Job Creation & Management
4. AI-Powered Resume Matching
5. Advanced Resume Filtering

**Phase 3 (Advanced Features):**
6. Candidate Tracking System
7. Manual Resume Rating System
8. Resume Match Rating & Ranking

**Phase 4 (Admin & Polish):**
9. Advanced User Management
10. Analytics & Reporting

---

## 🔄 Development Workflow for Each Feature

### Step 1: Create PRD
```bash
# Create PRD document
mkdir -p docs/prd
touch docs/prd/feature-name.md
# Fill in PRD template
```

### Step 2: Break Down into Stories
- Create user stories
- Define acceptance criteria
- Estimate effort per story

### Step 3: Create Feature Branch
```bash
git checkout main
git pull origin main
git checkout -b feature/feature-name
```

### Step 4: Implement Story by Story
- Implement one story at a time
- Write tests for each story
- Commit after each story completion

### Step 5: Create Pull Request
- Ensure all tests pass
- Update documentation
- Request code review

### Step 6: Address Review Comments
- Make requested changes
- Re-test
- Push updates

### Step 7: Merge and Deploy
- Merge to main after approval
- Deploy to staging
- Test in staging
- Deploy to production

---

## 11. Troubleshooting

### Common Issues:

#### Issue 1: Branch Already Exists

```bash
# Error: branch already exists
# Solution: Use a different name or delete old branch
git branch -d feature/old-branch-name
```

#### Issue 2: Merge Conflicts

```bash
# When pulling latest changes
git pull origin main

# If conflicts occur:
# 1. Open conflicted files
# 2. Look for <<<<<<< HEAD markers
# 3. Resolve conflicts manually
# 4. Stage resolved files
git add .
git commit -m "fix: resolve merge conflicts"
```

#### Issue 3: Forgot to Create Branch

```bash
# If you made changes on main by mistake
# Stash your changes
git stash

# Create proper branch
git checkout -b feature/your-feature

# Apply stashed changes
git stash pop
```

#### Issue 4: Need to Update Branch with Latest Main

```bash
# On your feature branch
git checkout feature/your-feature

# Pull latest main
git pull origin main

# Resolve any conflicts
# Then push
git push
```

#### Issue 5: Tests Failing

```bash
# Run tests to see what's failing
uv run python -m pytest tests/ -v

# Fix the issues
# Run tests again
# Commit fixes
```

---

## 📚 Additional Resources

### Learning Git:
- [Git Handbook](https://guides.github.com/introduction/git-handbook/)
- [Git Branching](https://learngitbranching.js.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

### Learning FastAPI:
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)

### Learning Python:
- [Python Official Docs](https://docs.python.org/3/)
- [Real Python](https://realpython.com/)

### Testing:
- [Pytest Documentation](https://docs.pytest.org/)
- [Testing FastAPI](https://fastapi.tiangolo.com/tutorial/testing/)

---

## 🎯 Quick Reference Commands

```bash
# Start working on a new feature
git checkout main
git pull origin main
git checkout -b feature/feature-name

# Check status
git status

# Stage and commit
git add .
git commit -m "feat: description"

# Push to GitHub
git push -u origin feature/feature-name

# Run tests
uv run python -m pytest tests/ -v

# Run application
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

---

## ✅ Checklist for Each Feature

Before creating a PR, ensure:

- [ ] Code runs without errors
- [ ] All tests pass
- [ ] Manual testing completed
- [ ] Code follows project style
- [ ] Comments added for complex logic
- [ ] No console errors or warnings
- [ ] Documentation updated (if needed)
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

---

## 🤝 Getting Help

If you're stuck:

1. **Check Documentation**
   - Read this guide
   - Check `README.md`
   - Review `DEPLOYMENT.md`

2. **Search Existing Code**
   - Look for similar implementations
   - Check how other features work

3. **Ask Your Senior**
   - Prepare specific questions
   - Share error messages
   - Explain what you've tried

4. **Use Git History**
   ```bash
   # See recent changes
   git log --oneline -10

   # See what changed in a file
   git log -p filename.py
   ```

---

## 🎉 You're Ready!

Pick a feature from the list above, create a branch, and start coding!

**Remember:**
- Start small
- Test frequently
- Commit often
- Ask questions
- Have fun! 🚀

**Good luck with your first contribution!**
