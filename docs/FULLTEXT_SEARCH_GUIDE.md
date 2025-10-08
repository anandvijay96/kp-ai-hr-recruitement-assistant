# Full-Text Search Implementation Guide

**Feature:** PostgreSQL Full-Text Search (FTS)  
**Date:** October 8, 2025  
**Status:** ✅ Implemented

---

## Overview

Implemented PostgreSQL Full-Text Search to enable fast, powerful searching across all candidate and resume data. Supports Boolean operators, phrase search, and weighted ranking.

---

## Features

### ✅ **Search Capabilities**

1. **Simple Search**
   ```
   "Python developer"
   ```
   Searches for candidates with both "Python" AND "developer"

2. **Boolean AND**
   ```
   "Python AND React"
   ```
   Finds candidates with both Python and React

3. **Boolean OR**
   ```
   "Java OR Kotlin"
   ```
   Finds candidates with either Java or Kotlin

4. **Boolean NOT**
   ```
   "Python NOT Django"
   ```
   Finds Python candidates excluding Django

5. **Phrase Search**
   ```
   "senior software engineer"
   ```
   Searches for exact phrase

6. **Complex Queries**
   ```
   "(Python OR Java) AND React NOT PHP"
   ```
   Advanced boolean combinations

---

## Database Schema

### **Added Columns**

```sql
-- Candidates table
ALTER TABLE candidates ADD COLUMN search_vector TSVECTOR;

-- Resumes table
ALTER TABLE resumes ADD COLUMN search_vector TSVECTOR;
```

### **GIN Indexes**

```sql
CREATE INDEX idx_candidates_search_vector ON candidates USING GIN(search_vector);
CREATE INDEX idx_resumes_search_vector ON resumes USING GIN(search_vector);
```

### **Auto-Update Triggers**

Automatically updates `search_vector` on INSERT or UPDATE:

**Candidates:**
- Full Name (Weight A - highest)
- Email (Weight B)
- Phone Number (Weight C)
- Location (Weight C)
- Professional Summary (Weight D)

**Resumes:**
- File Name (Weight B)
- Raw Text Content (Weight C)

---

## API Endpoints

### **1. Full-Text Search (GET)**

```http
GET /api/v1/candidates/full-text-search?q=Python+AND+React&page=1&page_size=20
```

**Query Parameters:**
- `q` (required): Search query string
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Results per page (default: 20)

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "skills": ["Python", "React", "JavaScript"],
      "experience_years": 5.2,
      "education": "Bachelor's",
      "status": "New",
      "resume_count": 1
    }
  ],
  "pagination": {
    "total": 15,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  },
  "search_query": "Python AND React"
}
```

### **2. Combined Search (POST)**

```http
POST /api/v1/candidates/search
Content-Type: application/json

{
  "search_query": "Python developer",
  "skills": ["React"],
  "min_experience": 3,
  "location": "New York"
}
```

Uses full-text search if `search_query` is provided, otherwise uses traditional filtering.

---

## Implementation Details

### **Query Parser**

The `_parse_search_query()` method converts user-friendly queries to PostgreSQL tsquery format:

| User Input | PostgreSQL tsquery |
|------------|-------------------|
| `Python developer` | `Python & developer` |
| `Python AND React` | `Python & React` |
| `Java OR Kotlin` | `Java \| Kotlin` |
| `NOT PHP` | `!PHP` |
| `"senior dev"` | `senior <-> dev` |

### **Search Vector Weights**

PostgreSQL FTS uses weights (A, B, C, D) to rank results:

- **A (Highest):** Full Name
- **B:** Email, File Name
- **C:** Phone, Location, Resume Text
- **D (Lowest):** Professional Summary

Results matching higher-weighted fields rank higher.

---

## Performance

### **Expected Performance**

- **< 2 seconds** for 10,000+ resumes
- **< 500ms** for typical queries (1,000 resumes)
- **GIN indexes** provide O(log n) search time

### **Optimization Tips**

1. **Use specific queries** instead of broad searches
2. **Combine with filters** to narrow results
3. **Limit page_size** for faster responses
4. **Monitor index size** - rebuild if fragmented

---

## Migration

### **Run Migration**

```bash
# Generate migration (already created)
alembic revision --autogenerate -m "add fulltext search support"

# Apply migration
alembic upgrade head
```

### **Verify Installation**

```sql
-- Check if columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name IN ('candidates', 'resumes') 
  AND column_name = 'search_vector';

-- Check if indexes exist
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename IN ('candidates', 'resumes') 
  AND indexname LIKE '%search_vector%';

-- Check if triggers exist
SELECT trigger_name, event_manipulation, event_object_table 
FROM information_schema.triggers 
WHERE trigger_name LIKE '%search_vector%';
```

---

## Usage Examples

### **Example 1: Find Python Developers**

```bash
curl "http://localhost:8000/api/v1/candidates/full-text-search?q=Python+developer"
```

### **Example 2: Find Java OR Kotlin Developers**

```bash
curl "http://localhost:8000/api/v1/candidates/full-text-search?q=Java+OR+Kotlin"
```

### **Example 3: Complex Query**

```bash
curl "http://localhost:8000/api/v1/candidates/full-text-search?q=(Python+OR+Java)+AND+React+NOT+PHP"
```

### **Example 4: Phrase Search**

```bash
curl 'http://localhost:8000/api/v1/candidates/full-text-search?q="senior+software+engineer"'
```

### **Example 5: Combined with Filters**

```bash
curl -X POST "http://localhost:8000/api/v1/candidates/search" \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "Python developer",
    "min_experience": 5,
    "location": "San Francisco"
  }'
```

---

## Testing

### **Test Query Parser**

```python
from services.filter_service import FilterService

fs = FilterService()

# Test simple query
assert fs._parse_search_query("Python developer") == "Python & developer"

# Test AND operator
assert fs._parse_search_query("Python AND React") == "Python & React"

# Test OR operator
assert fs._parse_search_query("Java OR Kotlin") == "Java | Kotlin"

# Test NOT operator
assert fs._parse_search_query("Python NOT Django") == "Python & !Django"

# Test phrase search
assert fs._parse_search_query('"senior developer"') == "senior <-> developer"
```

### **Test Full-Text Search**

```python
from core.database import SessionLocal
from services.filter_service import FilterService

db = SessionLocal()
fs = FilterService()

# Test search
results = fs.full_text_search("Python", db, page=1, page_size=10)
print(f"Found {results['pagination']['total']} candidates")
print(f"Results: {results['results']}")
```

---

## Troubleshooting

### **Issue: Search returns no results**

**Solution:**
1. Check if search_vector is populated:
   ```sql
   SELECT id, full_name, search_vector FROM candidates LIMIT 5;
   ```

2. Manually update search vectors:
   ```sql
   UPDATE candidates SET updated_at = NOW();
   UPDATE resumes SET uploaded_at = uploaded_at;
   ```

### **Issue: Slow search performance**

**Solution:**
1. Check if indexes exist:
   ```sql
   SELECT * FROM pg_indexes WHERE tablename = 'candidates';
   ```

2. Rebuild indexes:
   ```sql
   REINDEX INDEX idx_candidates_search_vector;
   REINDEX INDEX idx_resumes_search_vector;
   ```

3. Analyze tables:
   ```sql
   ANALYZE candidates;
   ANALYZE resumes;
   ```

### **Issue: Special characters in query**

**Solution:**
The query parser handles most special characters, but if issues occur:
- Escape special characters: `\(`, `\)`, `\&`
- Use phrase search for exact matches: `"exact phrase"`

---

## Next Steps

1. ✅ **Full-Text Search** - Implemented
2. ⏳ **Export Functionality** - Next task
3. ⏳ **Advanced Filter UI** - After export
4. ⏳ **Search Analytics** - Track popular queries

---

## References

- [PostgreSQL Full-Text Search Documentation](https://www.postgresql.org/docs/current/textsearch.html)
- [GIN Index Performance](https://www.postgresql.org/docs/current/gin-intro.html)
- [tsquery Syntax](https://www.postgresql.org/docs/current/datatype-textsearch.html)
