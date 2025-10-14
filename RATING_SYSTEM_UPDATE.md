# Rating System - One Rating Per User ✅

**Date:** October 15, 2025 - 12:50 AM IST  
**Status:** ✅ COMPLETE

---

## 🎯 **REQUIREMENT**

**Problem:** Users could create multiple ratings for the same candidate, causing:
- Duplicate ratings in history
- Incorrect average calculations
- Confusing user experience

**Solution:** One rating per user per candidate
- If user has no rating → Create new
- If user has existing rating → Update it
- Pre-fill form with existing values for editing

---

## 🔧 **IMPLEMENTATION**

### **1. Backend Changes**

**File:** `api/v1/ratings.py`

#### **A. Modified `/candidates/{candidate_id}/rate` endpoint:**

```python
# Check if user already has a rating for this candidate
stmt = select(CandidateRating).filter(
    CandidateRating.candidate_id == candidate_id,
    CandidateRating.user_id == user.id
)
result = await db.execute(stmt)
existing_rating = result.scalar_one_or_none()

if existing_rating:
    # Update existing rating
    existing_rating.technical_skills = rating_data.technical_skills
    existing_rating.communication = rating_data.communication
    # ... update all fields
    existing_rating.updated_at = datetime.utcnow()
    
    return {"message": "Rating updated successfully"}
else:
    # Create new rating
    rating = CandidateRating(...)
    db.add(rating)
    
    return {"message": "Rating created successfully"}
```

#### **B. Added new endpoint `/candidates/{candidate_id}/my-rating`:**

```python
@router.get("/candidates/{candidate_id}/my-rating")
async def get_my_rating(
    candidate_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current user's rating for a candidate"""
    # Returns existing rating or {"has_rating": False}
```

**Purpose:** Frontend can check if user already rated this candidate

---

### **2. Frontend Changes**

**File:** `templates/candidate_detail.html`

#### **Modified "Add Rating" button handler:**

**Before:**
```javascript
$('#addRatingBtn').click(() => {
    // Always reset form
    ratingData = { ... };
    $('#ratingForm')[0].reset();
    modal.show();
});
```

**After:**
```javascript
$('#addRatingBtn').click(async () => {
    // Check if user already has a rating
    const response = await fetch(`/api/v1/candidates/${candidateId}/my-rating`);
    const data = await response.json();
    
    if (data.has_rating) {
        // Pre-fill form with existing values
        ratingData = {
            technical_skills: data.technical_skills || 0,
            communication: data.communication || 0,
            culture_fit: data.culture_fit || 0,
            experience_level: data.experience_level || 0
        };
        
        $('#recommendation').val(data.recommendation || '');
        $('#ratingComments').val(data.comments || '');
        $('#strengths').val(data.strengths || '');
        $('#concerns').val(data.concerns || '');
        
        // Update modal title and button
        $('#ratingModal .modal-title').html('Edit Your Rating');
        $('#saveRatingBtn').html('Update Rating');
    } else {
        // Reset form for new rating
        ratingData = { ... };
        $('#ratingForm')[0].reset();
        
        $('#ratingModal .modal-title').html('Rate Candidate');
        $('#saveRatingBtn').html('Save Rating');
    }
    
    modal.show();
    
    // Set star values after modal opens
    setTimeout(() => {
        initStarRatings();
        // Update stars based on loaded data
        Object.keys(ratingData).forEach(category => {
            const value = ratingData[category];
            if (value > 0) {
                updateStars($rating, value);
            }
        });
    }, 100);
});
```

---

## ✅ **FEATURES**

### **1. Prevent Duplicate Ratings**
- ✅ Backend checks if user already rated
- ✅ Updates existing rating instead of creating new
- ✅ No duplicate entries in database

### **2. Edit Existing Rating**
- ✅ Modal title changes to "Edit Your Rating"
- ✅ Button text changes to "Update Rating"
- ✅ Form pre-filled with existing values
- ✅ Stars show current rating

### **3. Create New Rating**
- ✅ Modal title shows "Rate Candidate"
- ✅ Button text shows "Save Rating"
- ✅ Form is empty
- ✅ Stars are unselected

### **4. Correct Averages**
- ✅ Each user counted once
- ✅ Rating summary reflects actual unique ratings
- ✅ No inflated scores from duplicates

---

## 🎨 **USER EXPERIENCE**

### **Scenario 1: First Time Rating**
1. User clicks "Add Rating"
2. Modal opens with title "Rate Candidate"
3. Form is empty
4. User fills in rating
5. Clicks "Save Rating"
6. Success message: "Rating saved successfully!"

### **Scenario 2: Editing Existing Rating**
1. User clicks "Add Rating" (same button)
2. Backend detects existing rating
3. Modal opens with title "Edit Your Rating"
4. Form pre-filled with current values
5. Stars show current rating
6. User modifies rating
7. Clicks "Update Rating"
8. Success message: "Rating updated successfully!"

---

## 📊 **DATABASE BEHAVIOR**

### **Before (Problem):**
```
candidate_ratings table:
- id: 1, user_id: admin, candidate_id: 123, rating: 4
- id: 2, user_id: admin, candidate_id: 123, rating: 5  ❌ Duplicate!
- id: 3, user_id: admin, candidate_id: 123, rating: 3  ❌ Duplicate!

Average: (4 + 5 + 3) / 3 = 4.0  ❌ Wrong! Should be 3 (latest)
```

### **After (Fixed):**
```
candidate_ratings table:
- id: 1, user_id: admin, candidate_id: 123, rating: 3, updated_at: 2025-10-15

Average: 3.0  ✅ Correct! One rating per user
```

---

## 🔍 **TECHNICAL DETAILS**

### **API Endpoints:**

**1. POST `/api/v1/candidates/{candidate_id}/rate`**
- Creates new rating OR updates existing
- Returns: `{"message": "Rating created/updated successfully"}`

**2. GET `/api/v1/candidates/{candidate_id}/my-rating`**
- Returns current user's rating
- Response if exists:
  ```json
  {
    "has_rating": true,
    "id": "rating-id",
    "technical_skills": 4,
    "communication": 5,
    "culture_fit": 4,
    "experience_level": 5,
    "recommendation": "highly_recommended",
    "comments": "Great candidate",
    "strengths": "Strong technical skills",
    "concerns": "None",
    "created_at": "2025-10-15T00:00:00",
    "updated_at": "2025-10-15T00:30:00"
  }
  ```
- Response if doesn't exist:
  ```json
  {
    "has_rating": false
  }
  ```

**3. GET `/api/v1/candidates/{candidate_id}/ratings`**
- Returns all ratings (one per user)
- Used for rating history display

**4. GET `/api/v1/candidates/{candidate_id}/rating-summary`**
- Returns averages and statistics
- Now correctly calculates based on unique users

---

## ✅ **TESTING CHECKLIST**

- [x] User can create first rating ✅
- [x] User cannot create duplicate rating ✅
- [x] User can edit existing rating ✅
- [x] Form pre-fills with existing values ✅
- [x] Modal title changes appropriately ✅
- [x] Button text changes appropriately ✅
- [x] Stars show current rating when editing ✅
- [x] Average calculation is correct ✅
- [x] Rating history shows one per user ✅
- [x] Success message shows correct text ✅

---

## 🎉 **RESULT**

**Before:**
- ❌ Multiple ratings per user
- ❌ Duplicate entries in history
- ❌ Incorrect averages
- ❌ Confusing UX

**After:**
- ✅ One rating per user per candidate
- ✅ Clean rating history
- ✅ Correct averages
- ✅ Clear edit/create flow
- ✅ Professional UX

---

## 📝 **FILES CHANGED**

1. **`api/v1/ratings.py`**
   - Modified `create_rating()` to check for existing rating
   - Added `get_my_rating()` endpoint
   - Lines changed: ~60 lines

2. **`templates/candidate_detail.html`**
   - Modified Add Rating button handler
   - Added logic to pre-fill form
   - Added logic to update modal title/button
   - Lines changed: ~70 lines

**Total:** ~130 lines changed/added

---

## 🚀 **READY FOR DEMO**

The rating system now works correctly:
- ✅ No duplicate ratings
- ✅ Users can edit their rating
- ✅ Correct averages
- ✅ Professional UX
- ✅ Clear feedback

**Perfect for tomorrow's demo!** 🎉
