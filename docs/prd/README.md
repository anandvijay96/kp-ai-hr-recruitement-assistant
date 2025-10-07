# Product Requirements Documents (PRDs)

This directory contains all Product Requirements Documents for the AI HR Recruitment Assistant.

---

## 📚 Document Index

### High-Level Planning
- **[00-HIGH_LEVEL_PRD.md](./00-HIGH_LEVEL_PRD.md)** - Master PRD covering all features (2-10)
- **[PRD_TEMPLATE.md](./PRD_TEMPLATE.md)** - Template for creating detailed PRDs

---

## 🎯 Feature PRDs

### ✅ Completed Features
- **Feature 1: User Creation** - Being developed on separate branch (not in this repo)
- **Phase 0: Resume Authenticity Analysis** - Already implemented

### 📋 Planned Features (To Be Created)

#### Phase 1: Foundation (Weeks 1-6)
- [ ] **02-RESUME_UPLOAD_PRD.md** - Resume Upload & Data Extraction
- [ ] **03-RESUME_FILTER_PRD.md** - Advanced Resume Filtering

#### Phase 2: Tracking & Collaboration (Weeks 7-13)
- [ ] **04-CANDIDATE_TRACKING_PRD.md** - Candidate Tracking System
- [ ] **05-RESUME_RATING_PRD.md** - Manual Resume Rating System

#### Phase 3: Job Management & AI Matching (Weeks 14-21)
- [ ] **06-JOB_CREATION_PRD.md** - Job Creation & Management
- [ ] **07-AI_MATCHING_PRD.md** - AI-Powered Resume Matching
- [ ] **08-JOBS_DASHBOARD_PRD.md** - Jobs Dashboard & Management

#### Phase 4: Advanced Features (Weeks 22-27)
- [ ] **09-RESUME_RANKING_PRD.md** - Resume Match Rating & Ranking
- [ ] **10-USER_MANAGEMENT_PRD.md** - Advanced User Management

---

## 📊 Implementation Status

| Phase | Features | Status | Timeline |
|-------|----------|--------|----------|
| Phase 0 | Resume Authenticity | ✅ Complete | Completed |
| Phase 1 | Features 2-3 | 📋 Planning | Weeks 1-6 |
| Phase 2 | Features 4-5 | ⏳ Pending | Weeks 7-13 |
| Phase 3 | Features 6-8 | ⏳ Pending | Weeks 14-21 |
| Phase 4 | Features 9-10 | ⏳ Pending | Weeks 22-27 |

---

## 🔄 Development Workflow

For each feature, follow this process:

### 1. PRD Creation
```bash
# Create detailed PRD from high-level PRD
# Use PRD_TEMPLATE.md as base
# File: XX-FEATURE_NAME_PRD.md
```

### 2. Branch Creation
```bash
git checkout main
git pull origin main
git checkout -b feature/feature-name
```

### 3. Implementation
- Follow AI_DEVELOPMENT_GUIDE.md
- Break down into user stories
- Implement incrementally
- Write tests
- Document code

### 4. Review & Merge
- Create pull request
- Code review
- QA testing
- Merge to main

---

## 📝 PRD Guidelines

### When to Create a Detailed PRD
- Before starting implementation of any feature
- When breaking down high-level features into sub-features
- When significant changes are needed to existing features

### PRD Structure
Each detailed PRD should include:
1. **Overview** - Feature description and goals
2. **User Stories** - Detailed user stories with acceptance criteria
3. **Technical Requirements** - Architecture, APIs, database schema
4. **UI/UX Specifications** - Wireframes, mockups, user flows
5. **Success Metrics** - How to measure success
6. **Testing Strategy** - Unit, integration, and E2E tests
7. **Deployment Plan** - Rollout strategy and monitoring

### PRD Naming Convention
```
XX-FEATURE_NAME_PRD.md

Where:
- XX = Feature number (01-10)
- FEATURE_NAME = Descriptive name in UPPER_SNAKE_CASE
- Examples: 02-RESUME_UPLOAD_PRD.md, 07-AI_MATCHING_PRD.md
```

---

## 🎯 Priority Matrix

### P0 - Critical (Must Have)
- Feature 2: Resume Upload & Data Extraction
- Feature 3: Advanced Resume Filtering
- Feature 4: Candidate Tracking System
- Feature 6: Job Creation & Management
- Feature 7: AI-Powered Resume Matching

### P1 - High (Should Have)
- Feature 5: Manual Resume Rating System
- Feature 8: Jobs Dashboard & Management
- Feature 9: Resume Match Rating & Ranking
- Feature 10: Advanced User Management

---

## 📖 Related Documentation

- **[AI_DEVELOPMENT_GUIDE.md](../../AI_DEVELOPMENT_GUIDE.md)** - Development workflow and AI prompting
- **[CONTRIBUTING.md](../../CONTRIBUTING.md)** - Contribution guidelines
- **[README.md](../../README.md)** - Project overview
- **[DEPLOYMENT.md](../../DEPLOYMENT.md)** - Deployment instructions

---

## 🤝 Stakeholders

### Product Team
- Product Owner: [Name]
- Product Manager: [Name]

### Engineering Team
- Tech Lead: [Name]
- Backend Lead: [Name]
- Frontend Lead: [Name]
- QA Lead: [Name]

### Business Team
- Business Stakeholder: [Name]
- HR Lead: [Name]

---

## 📅 Review Schedule

- **Weekly:** Feature PRD reviews
- **Bi-weekly:** Implementation progress review
- **Monthly:** Product roadmap review
- **Quarterly:** Success metrics review

---

## 🔗 Quick Links

- [High-Level PRD](./00-HIGH_LEVEL_PRD.md)
- [PRD Template](./PRD_TEMPLATE.md)
- [Development Guide](../../AI_DEVELOPMENT_GUIDE.md)
- [Project Board](https://github.com/your-org/project/board) *(Update with actual link)*

---

**Last Updated:** October 6, 2025  
**Document Owner:** Product Management Team
