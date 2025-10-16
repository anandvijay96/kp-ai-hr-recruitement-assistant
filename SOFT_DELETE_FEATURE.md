# Soft Delete Feature for Candidates

**Status:** ✅ Backend Complete | 🔄 Frontend Pending  
**Date:** October 16, 2025

---

## **Overview**

Added soft delete functionality for candidates to allow admins to remove candidates from the UI while maintaining a complete audit trail in the database.

---

## **Backend Implementation**

### **1. Database Schema Changes**

**File:** `models/db/candidate.py`

**New Fields Added:**
```python
# Soft delete fields
is_deleted = Column(Boolean, default=False, nullable=False, index=True)
deleted_at = Column(DateTime(timezone=True), nullable=True)
deleted_by = Column(String(255), nullable=True)  # Admin username
deletion_reason = Column(Text, nullable=True)  # Optional reason
```

**Migration Required:**
```sql
ALTER TABLE candidates ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE candidates ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE candidates ADD COLUMN deleted_by VARCHAR(255);
ALTER TABLE candidates ADD COLUMN deletion_reason TEXT;
CREATE INDEX idx_candidates_is_deleted ON candidates(is_deleted);
```

---

### **2. API Endpoints**

**File:** `api/v1/candidates.py`

#### **Soft Delete Endpoint**
```
DELETE /api/v1/candidates/{candidate_id}/soft-delete?reason=optional&deleted_by=admin
```

**Response:**
```json
{
  "success": true,
  "message": "Candidate 'John Doe' deleted successfully",
  "candidate_id": 123,
  "deleted_at": "2025-10-16T17:00:00",
  "deleted_by": "admin"
}
```

#### **Restore Endpoint**
```
POST /api/v1/candidates/{candidate_id}/restore
```

**Response:**
```json
{
  "success": true,
  "message": "Candidate 'John Doe' restored successfully",
  "candidate_id": 123
}
```

---

### **3. Filter Service Updates**

**File:** `services/filter_service.py`

**Changes:**
- All search queries now exclude soft-deleted candidates
- Added filter: `Candidate.is_deleted == False`
- Applied to both `search_candidates()` and `full_text_search()`

**Result:** Deleted candidates are automatically hidden from all lists and searches

---

## **Frontend Implementation (TODO)**

### **1. Add Delete Button to Candidates List**

**File:** `templates/candidates.html`

**Location:** Add to each candidate card/row

**Example:**
```html
<button class="btn btn-sm btn-danger" 
        onclick="deleteCandidate(${candidate.id}, '${candidate.full_name}')">
    <i class="bi bi-trash"></i> Delete
</button>
```

---

### **2. Add JavaScript Function**

```javascript
async function deleteCandidate(candidateId, candidateName) {
    // Confirm deletion
    const confirmed = confirm(`Are you sure you want to delete "${candidateName}"?\n\nThis will remove them from the candidates list.`);
    
    if (!confirmed) return;
    
    // Optional: Ask for reason
    const reason = prompt('Optional: Enter reason for deletion:');
    
    try {
        const response = await fetch(`/api/v1/candidates/${candidateId}/soft-delete?reason=${encodeURIComponent(reason || '')}&deleted_by=admin`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            // Reload page or remove candidate from UI
            location.reload();
        } else {
            alert('Error: ' + data.detail);
        }
    } catch (error) {
        console.error('Delete error:', error);
        alert('Failed to delete candidate');
    }
}
```

---

### **3. Add to Candidate Detail Page**

**File:** `templates/candidate_detail.html`

**Location:** Add to header actions

```html
<div class="btn-group">
    <button class="btn btn-danger" onclick="deleteCandidate(${candidate.id}, '${candidate.full_name}')">
        <i class="bi bi-trash"></i> Delete Candidate
    </button>
</div>
```

---

## **Testing Instructions**

### **Step 1: Run Database Migration**

```bash
# Start Python shell
python

# Run migration
from core.database import engine, Base
from models.database import *
Base.metadata.create_all(bind=engine)
```

**Or manually:**
```sql
sqlite3 hr_recruitment.db

ALTER TABLE candidates ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE candidates ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE candidates ADD COLUMN deleted_by VARCHAR(255);
ALTER TABLE candidates ADD COLUMN deletion_reason TEXT;
CREATE INDEX idx_candidates_is_deleted ON candidates(is_deleted);
```

---

### **Step 2: Test API Endpoints**

```bash
# Test soft delete
curl -X DELETE "http://localhost:8000/api/v1/candidates/1/soft-delete?reason=Test&deleted_by=admin"

# Verify candidate is hidden
curl "http://localhost:8000/api/v1/candidates/search" -H "Content-Type: application/json" -d '{}'

# Test restore
curl -X POST "http://localhost:8000/api/v1/candidates/1/restore"
```

---

### **Step 3: Add Frontend UI**

1. Add delete button to candidates list
2. Add JavaScript function
3. Test deletion flow
4. Verify candidate disappears from list
5. Check database to confirm soft delete (not hard delete)

---

## **Audit Trail**

All deletions are tracked with:
- ✅ **Who deleted:** `deleted_by` field
- ✅ **When deleted:** `deleted_at` timestamp
- ✅ **Why deleted:** `deletion_reason` (optional)
- ✅ **Restoration capability:** Can be restored via API

**Query deleted candidates:**
```sql
SELECT id, full_name, email, deleted_at, deleted_by, deletion_reason
FROM candidates
WHERE is_deleted = TRUE
ORDER BY deleted_at DESC;
```

---

## **Benefits**

1. **Data Preservation:** No data loss, can restore if needed
2. **Audit Trail:** Complete history of who deleted what and when
3. **Clean UI:** Deleted candidates don't clutter the interface
4. **Compliance:** Meets data retention requirements
5. **Reversible:** Mistakes can be undone

---

## **Next Steps**

1. ✅ Backend implementation complete
2. 🔄 Add frontend UI (delete button + JavaScript)
3. 🔄 Test full flow: delete → verify hidden → restore
4. 🔄 Re-upload candidates with new LLM extraction
5. 🔄 Verify candidate detail page shows correct data
6. ✅ Close Phase 2

---

## **Related Files**

- `models/db/candidate.py` - Database schema
- `api/v1/candidates.py` - API endpoints
- `services/filter_service.py` - Search filtering
- `templates/candidates.html` - Frontend UI (TODO)
- `templates/candidate_detail.html` - Detail page (TODO)

---

**Ready for frontend implementation!** 🚀
