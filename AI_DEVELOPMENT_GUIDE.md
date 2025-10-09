# 🚀 AI-Assisted Development Guide

This guide provides prompting techniques and workflows for efficient AI-assisted development using tools like Cursor, Windsurf, and other AI-powered IDEs.

---

## 📋 Table of Contents
1. [Development Workflow](#development-workflow)
2. [PRD Creation Prompts](#prd-creation-prompts)
3. [Technical Implementation Prompts](#technical-implementation-prompts)
4. [Working with AI Tools](#working-with-ai-tools)
5. [Feature Implementation Priority](#feature-implementation-priority)
6. [Quality Assurance](#quality-assurance)

---

## 🚀 Development Workflow

### **Phase 1: Preparation**
1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Create PRD Document**
   - Create `docs/prd/XX-feature-name.md`
   - Use the PRD creation prompts below

### **Phase 2: Development**
3. **Implement User Stories**
   - One story at a time
   - Write tests for each story
   - Commit after each story

4. **Code Quality**
   - Run tests: `uv run python -m pytest tests/ -v`
   - Check for errors
   - Update documentation

### **Phase 3: Review & Merge**
5. **Create Pull Request**
   - Ensure all tests pass
   - Request code review
   - Address feedback

6. **Merge & Deploy**
   - After approval, merge to main
   - Deploy and test

---

## 🎯 PRD Creation Prompts

### **📝 Prompt 1: Create Complete PRD**
```
You are a senior product manager creating a comprehensive Product Requirements Document (PRD) for a new feature in our HR recruitment application.

Create a detailed PRD for: [FEATURE NAME]

Structure the PRD with these sections:

1. OVERVIEW
   - Brief description of what this feature does
   - Problem statement it solves
   - Target users (recruiters, admins, etc.)

2. USER STORIES
   - Write 3-5 user stories in "As a... I want... So that..." format
   - Each story should be specific and testable

3. ACCEPTANCE CRITERIA
   - List specific, measurable criteria for each user story
   - Include both functional and non-functional requirements

4. TECHNICAL DESIGN
   - Database schema (tables, columns, relationships)
   - API endpoints needed (HTTP methods, paths, request/response)
   - UI components and user flow
   - Integration points with existing system

5. DEPENDENCIES
   - External libraries or services needed
   - Internal modules that need modification
   - Any prerequisites

6. TESTING PLAN
   - Unit tests needed
   - Integration tests needed
   - Manual testing scenarios
   - Edge cases to consider

7. IMPLEMENTATION PLAN
   - Break down into 2-3 phases with specific tasks
   - Estimate effort for each phase
   - Identify risks and mitigation strategies

8. SUCCESS METRICS
   - How we'll measure if this feature is successful
   - Key performance indicators

Make this PRD comprehensive but actionable - detailed enough for a developer to implement from, but not overwhelming.
```

### **📝 Prompt 2: Technical Implementation Planning**
```
You are a senior software architect planning the technical implementation for a new feature in our HR application.

For the feature: [FEATURE NAME]

Provide detailed technical specifications:

1. DATABASE DESIGN
   - Design the database schema
   - Specify table names, column types, constraints
   - Define relationships and indexes

2. API DESIGN
   - List all required endpoints
   - Specify HTTP methods, paths, and parameters
   - Define request/response schemas using Pydantic models

3. SERVICE LAYER
   - Identify services needed
   - Define service methods and their responsibilities
   - Specify business logic implementation

4. UI/UX DESIGN
   - Describe the user interface components
   - Specify templates and static files needed
   - Define user interactions and flows

5. INTEGRATION POINTS
   - How this feature integrates with existing modules
   - What existing APIs or services it uses
   - Any modifications needed to current codebase

6. FILE STRUCTURE
   - List all new files to be created
   - Specify which existing files need modification
   - Suggest file organization

7. TESTING STRATEGY
   - Unit tests for services and utilities
   - Integration tests for API endpoints
   - Manual testing checklist

8. DEPLOYMENT CONSIDERATIONS
   - Any special deployment requirements
   - Environment variables or configuration needed
   - Migration scripts if database changes

Focus on making this implementable - provide concrete examples of code structure, API responses, and database queries.
```

### **📝 Prompt 3: Code Implementation**
```
You are an expert Senior developer implementing a new feature for an HR recruitment application.

Implement the following feature based on the PRD: [FEATURE NAME]

Requirements:
- Follow FastAPI best practices
- Use async/await where appropriate
- Include proper error handling
- Add comprehensive logging
- Write tests for all functionality
- Use existing project patterns and conventions

Implementation checklist:
- [ ] Create/update database models
- [ ] Implement service layer logic
- [ ] Create API endpoints with proper validation
- [ ] Add HTML templates with responsive design
- [ ] Write unit and integration tests
- [ ] Update documentation
- [ ] Test manually to ensure functionality works

Focus on clean, maintainable code that follows the existing codebase patterns. Include proper type hints, docstrings, and error handling.
```

---

## 🛠️ Working with AI Development Tools

### **For Cursor/Windsurf Users:**

#### **🔧 Setup Prompt**
```
Set up my development environment for implementing a new feature:

1. Current branch: [BRANCH NAME]
2. Feature: [FEATURE NAME]
3. Project structure: FastAPI with Jinja2 templates

Help me:
- Verify I'm on the correct branch
- Set up the file structure for this feature
- Create any necessary directories
- Check current project dependencies
- Start the development server for testing
```

#### **📁 File Creation Prompt**
```
Create the necessary files for implementing [FEATURE NAME]:

Based on the PRD, I need these files:
- Models: [list database models]
- Services: [list service classes]
- API endpoints: [list API routes]
- Templates: [list HTML templates]
- Tests: [list test files]

For each file, create the basic structure with:
- Proper imports
- Class/function definitions
- Type hints
- Docstrings
- Basic error handling

Start with the most fundamental files (models first, then services, then API, then UI).
```

#### **⚡ Quick Implementation Prompt**
```
Implement the core functionality for [FEATURE NAME]:

Using the PRD specifications, implement:
1. Database models with proper relationships
2. Service methods with business logic
3. API endpoints with validation
4. Basic HTML templates

Focus on getting the core functionality working first, then we can enhance and polish. Include proper error handling and logging throughout.
```

#### **🧪 Testing Prompt**
```
Create comprehensive tests for the [FEATURE NAME] implementation:

Write tests for:
- All service methods
- All API endpoints
- Database operations
- Error scenarios
- Edge cases

Use pytest conventions and ensure good test coverage. Include both unit tests and integration tests where appropriate.
```

---

## 📊 Feature Implementation Priority

### **Phase 1 (Foundation)**
1. **User Authentication & Management**
2. **Enhanced Resume Upload & Processing**

### **Phase 2 (Core Features)**
3. **Job Creation & Management**
4. **AI-Powered Resume Matching**
5. **Advanced Resume Filtering**

### **Phase 3 (Advanced Features)**
6. **Candidate Tracking System**
7. **Manual Resume Rating System**
8. **Resume Match Rating & Ranking**

### **Phase 4 (Admin & Polish)**
9. **Advanced User Management**
10. **Analytics & Reporting**

---

## 🔄 Standard Branch Naming Convention

```
feature/feature-name           # New features
bugfix/issue-description       # Bug fixes
enhancement/improvement-name   # Improvements
refactor/module-name          # Code refactoring
docs/documentation-update     # Documentation changes
```

---

## ✅ Quality Assurance

### **Pre-PR Checklist**
- [ ] Code runs without errors
- [ ] All tests pass (`pytest` green)
- [ ] Manual testing completed
- [ ] No console errors or warnings
- [ ] Follows project code style
- [ ] Proper error handling included
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### **Testing Commands**
```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test file
uv run python -m pytest tests/test_feature.py -v

# Run with coverage
uv run python -m pytest tests/ --cov=. --cov-report=html

# Start development server
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### **Manual Testing Checklist**
- [ ] Feature works as expected
- [ ] Error handling works properly
- [ ] UI is responsive and accessible
- [ ] Integration with existing features works
- [ ] Performance is acceptable
- [ ] No security vulnerabilities

---

## 🚨 Troubleshooting

### **Common Issues**

#### **Issue 1: Branch Conflicts**
```bash
# Pull latest changes
git pull origin main

# If conflicts occur:
# 1. Open conflicted files
# 2. Look for <<<<<<< HEAD markers
# 3. Resolve conflicts manually
# 4. Stage resolved files
git add .
git commit -m "fix: resolve merge conflicts"
```

#### **Issue 2: Tests Failing**
```bash
# Run tests to see what's failing
uv run python -m pytest tests/ -v

# Check specific failing test
uv run python -m pytest tests/test_specific.py::test_function -v

# Fix the issues and run again
```

#### **Issue 3: Import Errors**
```bash
# Check if dependencies are installed
uv sync

# Verify Python path and imports
python -c "import sys; print(sys.path)"

# Check for circular imports
# Look for import statements in files
```

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

## 📚 Additional Resources

### **Learning Resources:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)

### **Best Practices:**
- [Clean Code Principles](https://blog.cleancoder.com/uncle-bob/2013/09/23/Why-Clean-Code.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [REST API Design](https://restfulapi.net/)

---

**This guide provides everything needed for efficient AI-assisted development. Use the prompts as starting points and customize them for your specific needs.**
