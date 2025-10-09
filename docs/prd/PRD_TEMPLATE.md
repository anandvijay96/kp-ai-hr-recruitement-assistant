# Feature: [Feature Name]

**Author:** [Your Name]  
**Date:** [YYYY-MM-DD]  
**Status:** Draft | In Review | Approved | In Development | Completed  
**Priority:** High | Medium | Low  

---

## 📋 Overview

Brief description of what this feature does and why it's needed.

**Problem Statement:**
What problem does this feature solve?

**Target Users:**
Who will use this feature? (Recruiters, Admins, Candidates, etc.)

---

## 🎯 Goals & Objectives

**Primary Goals:**
- Goal 1
- Goal 2
- Goal 3

**Success Metrics:**
- Metric 1: [How to measure]
- Metric 2: [How to measure]
- Metric 3: [How to measure]

---

## 👥 User Stories

### Story 1: [Title]
**As a** [user type]  
**I want** [goal]  
**So that** [benefit]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Priority:** High | Medium | Low  
**Estimated Effort:** X hours/days

---

### Story 2: [Title]
**As a** [user type]  
**I want** [goal]  
**So that** [benefit]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Priority:** High | Medium | Low  
**Estimated Effort:** X hours/days

---

## 🎨 UI/UX Design

### Wireframes/Mockups
[Add links to Figma, screenshots, or describe the UI]

### User Flow
```
Step 1: User lands on page X
  ↓
Step 2: User clicks button Y
  ↓
Step 3: System does Z
  ↓
Step 4: User sees result
```

### Key UI Elements
- Element 1: Description
- Element 2: Description
- Element 3: Description

---

## 🔧 Technical Design

### Architecture Overview
[Describe high-level architecture]

### Database Schema

**New Tables:**
```sql
CREATE TABLE table_name (
    id SERIAL PRIMARY KEY,
    field1 VARCHAR(255),
    field2 INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Modified Tables:**
- Table 1: Add columns X, Y
- Table 2: Add index on column Z

### API Endpoints

#### Endpoint 1: Create Resource
```
POST /api/resource
Request Body:
{
    "field1": "value",
    "field2": 123
}

Response: 201 Created
{
    "id": "uuid",
    "field1": "value",
    "field2": 123
}
```

#### Endpoint 2: Get Resource
```
GET /api/resource/{id}

Response: 200 OK
{
    "id": "uuid",
    "field1": "value",
    "field2": 123
}
```

### Services/Components

**New Services:**
- `ServiceName`: Description of what it does

**Modified Services:**
- `ExistingService`: What changes are needed

### Data Flow
```
User Action
  ↓
Frontend (templates/page.html)
  ↓
API Endpoint (api/endpoint.py)
  ↓
Service Layer (services/service.py)
  ↓
Database
  ↓
Response back to user
```

---

## 📦 Dependencies

### External Libraries
- Library 1: Purpose
- Library 2: Purpose

### External Services
- Service 1: Purpose (API keys needed?)
- Service 2: Purpose

### Internal Dependencies
- Feature X must be completed first
- Requires changes to Module Y

---

## 🧪 Testing Plan

### Unit Tests
- [ ] Test service method A
- [ ] Test service method B
- [ ] Test validation logic

### Integration Tests
- [ ] Test API endpoint flow
- [ ] Test database operations
- [ ] Test external service integration

### Manual Testing Scenarios

**Scenario 1: Happy Path**
1. Step 1
2. Step 2
3. Expected result

**Scenario 2: Error Handling**
1. Step 1
2. Step 2
3. Expected error message

**Scenario 3: Edge Case**
1. Step 1
2. Step 2
3. Expected behavior

### Performance Testing
- Load test with X concurrent users
- Response time should be < Y ms
- Database queries optimized

---

## 🚀 Implementation Plan

### Phase 1: Foundation (Week 1)
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

### Phase 2: Core Features (Week 2)
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

### Phase 3: Polish & Testing (Week 3)
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

**Total Estimated Time:** X weeks

---

## ⚠️ Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Risk 1 | High/Medium/Low | High/Medium/Low | How to mitigate |
| Risk 2 | High/Medium/Low | High/Medium/Low | How to mitigate |

---

## 🔒 Security Considerations

- Security concern 1 and how to address it
- Security concern 2 and how to address it
- Authentication/Authorization requirements

---

## ♿ Accessibility

- Accessibility requirement 1
- Accessibility requirement 2
- WCAG compliance level

---

## 📱 Mobile Considerations

- How will this work on mobile?
- Responsive design requirements
- Touch interactions

---

## 🌍 Internationalization (i18n)

- Languages to support
- Text that needs translation
- Date/time formatting

---

## 📊 Analytics & Monitoring

**Events to Track:**
- Event 1: When user does X
- Event 2: When system does Y

**Metrics to Monitor:**
- Metric 1: Description
- Metric 2: Description

**Alerts:**
- Alert if error rate > X%
- Alert if response time > Y ms

---

## 📚 Documentation

**User Documentation:**
- [ ] User guide for feature
- [ ] FAQ section
- [ ] Video tutorial (if needed)

**Developer Documentation:**
- [ ] API documentation
- [ ] Code comments
- [ ] Architecture diagrams

---

## 🔄 Migration Plan

**If modifying existing feature:**
- Data migration steps
- Backward compatibility
- Rollback plan

---

## ✅ Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Manual testing completed
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Deployed to staging
- [ ] Stakeholder approval
- [ ] Deployed to production
- [ ] Monitoring in place

---

## 📝 Notes & Open Questions

**Questions:**
1. Question 1?
2. Question 2?

**Decisions Made:**
- Decision 1: Rationale
- Decision 2: Rationale

**Future Enhancements:**
- Enhancement 1
- Enhancement 2

---

## 📎 References

- Link to design mockups
- Link to related PRDs
- Link to technical specs
- Link to research/data
