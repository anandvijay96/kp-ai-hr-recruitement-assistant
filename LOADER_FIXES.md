# Infinite Loader Fixes

## Issues Found:

### 1. Dashboard - Missing API Endpoint
**Problem:** Dashboard tries to fetch from `/api/v1/dashboard/hr` which doesn't exist
**Solution:** Create mock endpoint or fix dashboard to use existing endpoints

### 2. Candidates List - Wrong Auth Method
**Problem:** Uses token-based auth (`Bearer token`) but app uses session-based auth
**Solution:** Remove token requirement, use session cookies

## Fixes Applied:

### Fix 1: Candidates List - Remove Token Auth
File: `templates/candidates/list.html`
- Remove localStorage token checks
- Remove Authorization header
- Use session-based auth (cookies)

### Fix 2: Dashboard - Create Mock Endpoint
File: `api/v1/dashboard.py` (create new)
- Create basic dashboard endpoint
- Return mock data for now
- Register router in main.py
