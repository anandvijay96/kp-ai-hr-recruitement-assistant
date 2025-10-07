# 🚀 Quick Start Guide - Integrated HRMS Portal

## Start Testing in 3 Steps

### Step 1: Start the Server
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 2: Open Your Browser
Navigate to the **Home Page**:
```
http://localhost:8000/
```

### Step 3: Explore the Features!

## 🎯 Feature Testing Guide

### Feature 1: Resume Analysis (Single)

1. Click "Resume Analysis" in navigation
2. Upload a resume file (PDF, DOC, or DOCX)
3. (Optional) Paste a job description
4. Click "Analyze Resume"
5. ✅ View authenticity scores and JD matching results

### Feature 2: Batch Resume Analysis with JD Matching
1. Go to "Resume Analysis"
2. Scroll to "Batch Resume Analysis"
3. Select multiple resume files
4. **NEW:** Paste job description (applies to all resumes)
5. Click "Analyze Multiple Resumes"
6. ✅ View summary and individual results with JD scores

### Feature 3: Candidate Database Filtering

#### Scenario 1: Find Python Developers
1. Go to "Candidate Database"
2. Check "Python" in the Skills section
3. Click "Apply Filters"
4. ✅ You should see 3 candidates (John, Bob, Charlie)

#### Scenario 2: Find Senior Candidates (5+ years)
1. Set "Min" experience to 5
2. Click "Apply Filters"
3. ✅ You should see 2 candidates (John, Bob)

#### Scenario 3: Find Advanced Degree Holders
1. Check "Master's" and "PhD" in Education
2. Click "Apply Filters"
3. ✅ You should see 2 candidates (Jane, Alice)

## 📊 Mock Data Available

| Name | Skills | Experience | Education | Status |
|------|--------|------------|-----------|--------|
| John Doe | Python, Java | 5 years | Bachelor's | New |
| Jane Smith | JavaScript, React | 3 years | Master's | Screened |
| Bob Johnson | Python, SQL | 7 years | Bachelor's | New |
| Alice Williams | Java, SQL | 4 years | PhD | Interviewed |
| Charlie Brown | Python, JavaScript | 2 years | Bachelor's | New |

## 🔗 All Pages

- **Home:** http://localhost:8000/
- **Resume Analysis:** http://localhost:8000/upload
- **Candidate Database:** http://localhost:8000/candidates
- **API Docs:** http://localhost:8000/docs

## ✨ What's New in This Integration

- ✅ **Unified Navigation** - Consistent navbar across all pages
- ✅ **Bootstrap Styling** - Professional, consistent design
- ✅ **JD Matching for Batch** - Apply job description to multiple resumes
- ✅ **Improved Candidate Cards** - Better visual presentation
- ✅ **Proper Feature Separation** - Analysis vs. Database views
- ✅ **Responsive Design** - Works on all screen sizes

## 🧪 Run Tests

```bash
# All tests
pytest tests/ -v

# Filter tests only
pytest tests/test_filters.py -v
```

## 📚 Full Documentation

See `docs/TESTING_GUIDE.md` for comprehensive testing instructions.
See `docs/PHASE_COMPLETE_SUMMARY.md` for implementation details.

---

**That's it! You're ready to test the Advanced Resume Filtering feature! 🎉**
