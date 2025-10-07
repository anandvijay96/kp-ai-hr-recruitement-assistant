# Testing Guide: Advanced Resume Filtering Feature

## Quick Start

### 1. Start the Application

```bash
# Using UV (recommended)
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Using pip
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Access the Candidate Dashboard

Open your browser and navigate to:
```
http://localhost:8000/candidates
```

## Features to Test

### Filter Panel (Left Sidebar)

1. **Keywords Search**
   - Enter keywords in the search box
   - Click "Apply Filters" to search

2. **Skills Filter**
   - Check/uncheck skills: Python, Java, JavaScript, SQL
   - Multiple selections supported
   - Click "Apply Filters" to see results

3. **Experience Filter**
   - Set minimum years (0-30)
   - Set maximum years (0-30)
   - Click "Apply Filters"

4. **Education Filter**
   - Select: Bachelor's, Master's, PhD
   - Multiple selections supported

5. **Location Filter**
   - Select from dropdown: New York, San Francisco, Austin
   - Or select "All Locations"

6. **Clear Filters**
   - Click "Clear Filters" to reset all filters

### Results Panel (Right Side)

1. **Candidate Cards**
   - View candidate name, email, skills, experience, education
   - Status badge shows candidate status
   - Hover effect on cards

2. **Pagination**
   - Navigate through pages if more than 20 results
   - Current page is disabled/highlighted

3. **Action Buttons**
   - "View Profile" button (placeholder)
   - "Shortlist" button (placeholder)

## API Testing

### Test Endpoints with curl

**1. Search Candidates (No Filters)**
```bash
curl -X POST "http://localhost:8000/api/v1/candidates/search" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**2. Filter by Skills**
```bash
curl -X POST "http://localhost:8000/api/v1/candidates/search" \
  -H "Content-Type: application/json" \
  -d '{"skills": ["Python"]}'
```

**3. Filter by Experience**
```bash
curl -X POST "http://localhost:8000/api/v1/candidates/search" \
  -H "Content-Type: application/json" \
  -d '{"min_experience": 3, "max_experience": 6}'
```

**4. Combined Filters**
```bash
curl -X POST "http://localhost:8000/api/v1/candidates/search" \
  -H "Content-Type: application/json" \
  -d '{"skills": ["Python"], "education": ["Bachelor'\''s", "Master'\''s"]}'
```

**5. Get Filter Options**
```bash
curl "http://localhost:8000/api/v1/candidates/filter-options"
```

**6. Create Filter Preset**
```bash
curl -X POST "http://localhost:8000/api/v1/candidates/filter-presets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Senior Python Developers",
    "filters": {
      "skills": ["Python"],
      "min_experience": 5
    }
  }'
```

**7. Get Filter Presets**
```bash
curl "http://localhost:8000/api/v1/candidates/filter-presets"
```

## Mock Data

The system includes 5 mock candidates for testing:

1. **John Doe** - Python, Java | 5 years | Bachelor's | New
2. **Jane Smith** - JavaScript, React | 3 years | Master's | Screened
3. **Bob Johnson** - Python, SQL | 7 years | Bachelor's | New
4. **Alice Williams** - Java, SQL | 4 years | PhD | Interviewed
5. **Charlie Brown** - Python, JavaScript | 2 years | Bachelor's | New

## Test Scenarios

### Scenario 1: Find Python Developers
1. Check "Python" in Skills filter
2. Click "Apply Filters"
3. **Expected:** See John Doe, Bob Johnson, Charlie Brown

### Scenario 2: Find Senior Candidates (5+ years)
1. Set Min Experience to 5
2. Click "Apply Filters"
3. **Expected:** See John Doe, Bob Johnson

### Scenario 3: Find Master's or PhD Holders
1. Check "Master's" and "PhD" in Education
2. Click "Apply Filters"
3. **Expected:** See Jane Smith, Alice Williams

### Scenario 4: Combined Filters
1. Check "Python" in Skills
2. Set Min Experience to 3
3. Check "Bachelor's" in Education
4. Click "Apply Filters"
5. **Expected:** See John Doe, Bob Johnson

### Scenario 5: Clear All Filters
1. Apply any filters
2. Click "Clear Filters"
3. **Expected:** See all 5 candidates

## Running Automated Tests

```bash
# Run all tests
pytest tests/ -v

# Run only filter tests
pytest tests/test_filters.py -v

# Run with coverage
pytest tests/test_filters.py --cov=services.filter_service --cov-report=html
```

## Known Limitations (MVP)

1. **Mock Data:** Currently using in-memory mock data (5 candidates)
2. **No Database:** Data doesn't persist between server restarts
3. **No Authentication:** No user login required
4. **Placeholder Actions:** View Profile and Shortlist buttons are placeholders
5. **Basic Pagination:** Simple pagination without advanced controls

## Next Steps for Production

1. Connect to PostgreSQL database
2. Implement full-text search with PostgreSQL FTS
3. Add user authentication and authorization
4. Implement actual View Profile and Shortlist functionality
5. Add advanced filters (rating, status, date ranges)
6. Implement filter preset sharing
7. Add export functionality (CSV, PDF)
8. Performance optimization for large datasets (10,000+ candidates)

## Troubleshooting

**Issue:** No candidates showing
- **Solution:** Check browser console for errors, ensure API is running

**Issue:** Filters not working
- **Solution:** Clear browser cache, check network tab for API responses

**Issue:** Port already in use
- **Solution:** Use a different port: `uvicorn main:app --port 8001`

**Issue:** Import errors
- **Solution:** Ensure all dependencies are installed: `pip install -r requirements.txt`
