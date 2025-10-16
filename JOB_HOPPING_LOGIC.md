# 🎯 Job Hopping Detection Logic

## **Critical Fix: Internal Promotions vs Job Changes**

### **Problem (Before):**
```
Candidate worked at Innova Solutions:
- Junior Software Engineer: 11 months
- Trainee Software Engineer: 6 months

❌ WRONG: Counted as 2 job hops (both < 12 months)
```

### **Solution (After):**
```
Candidate worked at Innova Solutions:
- Junior Software Engineer: 11 months
- Trainee Software Engineer: 6 months
- Total at Innova Solutions: 17 months

✅ CORRECT: Counted as 0 job hops (17 months at same company)
```

---

## **How It Works:**

### **1. Company-Level Aggregation**
```python
# Group all roles by company (case-insensitive)
company_tenures = {
    'innova solutions': {
        'total_duration': 17,  # 11 + 6 months
        'roles': [
            {'title': 'Junior Software Engineer', 'duration': 11},
            {'title': 'Trainee Software Engineer', 'duration': 6}
        ]
    }
}
```

### **2. Job Hopping Detection**
- **Only counts company changes**, not role changes
- **Short stint = < 12 months at a company**
- **Internal promotions are ignored**

### **3. Risk Calculation**
```
0 short stints  → No risk, 0 penalty
1 short stint   → Low risk, -3 points
2 short stints  → Medium risk, -7 points
3+ short stints → High risk, -12 points
```

---

## **Examples:**

### **Example 1: Internal Growth (NOT Job Hopping)**
```
Work History:
1. Innova Solutions
   - Junior Software Engineer: 11 months
   - Trainee Software Engineer: 6 months
   Total: 17 months

Result:
✅ 0 job hops
✅ 0 penalty
✅ Shows career growth within same company
```

### **Example 2: Actual Job Hopping**
```
Work History:
1. Company A: 8 months
2. Company B: 10 months
3. Company C: 6 months

Result:
❌ 3 job hops (all < 12 months)
❌ -12 points penalty
❌ High risk - frequent company changes
```

### **Example 3: Mixed Pattern**
```
Work History:
1. Company A: 24 months (stable)
2. Company B: 8 months (short)
3. Company C: 18 months (stable)

Result:
⚠️ 1 job hop
⚠️ -3 points penalty
⚠️ Low risk - mostly stable with one short stint
```

---

## **Display Format:**

### **When Job Hopping Detected:**
```
📋 Job Hopping Analysis
Risk Level: MEDIUM
Score Impact: -7 points
Short Stints: 2 of 5 companies
Average Tenure: 14 months
Career Level: mid-level

Pattern: 2 of 5 companies < 12 months

Recent Short Stints:
• Junior Software Engineer, Trainee Software Engineer: Company A, 8 months
• Developer: Company B, 10 months

💡 Recommendation: Moderate concern. 2 short stints detected. 
Discuss reasons for job changes during interview.
```

### **When No Job Hopping:**
```
✅ No job hopping section displayed
✅ Job Hopping Impact: 0 pts
✅ Final Score = Base Score (no penalty)
```

---

## **Key Features:**

1. ✅ **Company-level aggregation** - Combines all roles at same company
2. ✅ **Case-insensitive matching** - "Innova Solutions" = "innova solutions"
3. ✅ **Handles internal promotions** - Shows all role titles in display
4. ✅ **Career level awareness** - Junior/Mid/Senior classification
5. ✅ **Detailed recommendations** - Context-aware advice for HR

---

## **Technical Implementation:**

**File:** `api/v1/vetting.py`  
**Function:** `_analyze_job_hopping()`

**Algorithm:**
1. Extract all work experience entries
2. Group by company name (normalized to lowercase)
3. Sum durations for each company
4. Identify companies with < 12 months total tenure
5. Calculate risk level and score impact
6. Generate detailed recommendation

**Edge Cases Handled:**
- ✅ `duration_months = None` → Treated as 0
- ✅ Same company, different capitalization → Merged
- ✅ Multiple roles at same company → Aggregated
- ✅ No work experience → Returns safe defaults

---

## **Benefits:**

### **For HR Team:**
- ✅ **Accurate assessment** - No false positives from internal growth
- ✅ **Clear insights** - See actual company changes, not role changes
- ✅ **Better decisions** - Distinguish career growth from job hopping

### **For Candidates:**
- ✅ **Fair evaluation** - Internal promotions are rewarded, not penalized
- ✅ **Career growth recognized** - Multiple roles at same company show progression
- ✅ **Accurate representation** - True job stability is measured

---

## **Testing:**

**Test Case 1: Internal Promotion**
```python
work_experience = [
    {'company': 'Innova Solutions', 'title': 'Junior Engineer', 'duration_months': 11},
    {'company': 'Innova Solutions', 'title': 'Trainee Engineer', 'duration_months': 6}
]

Expected:
- total_companies: 1
- short_tenures: 0 (17 months total)
- risk_level: 'none'
- score_impact: 0
```

**Test Case 2: Actual Job Hopping**
```python
work_experience = [
    {'company': 'Company A', 'title': 'Developer', 'duration_months': 8},
    {'company': 'Company B', 'title': 'Developer', 'duration_months': 10},
    {'company': 'Company C', 'title': 'Developer', 'duration_months': 6}
]

Expected:
- total_companies: 3
- short_tenures: 3
- risk_level: 'high'
- score_impact: -12
```

---

**Status: ✅ IMPLEMENTED & TESTED**  
**Last Updated:** Oct 16, 2025  
**Version:** 1.0
