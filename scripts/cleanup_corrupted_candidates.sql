-- Cleanup Script for Corrupted Candidate Data
-- Run this to remove candidates with corrupted work experience/education data
-- Created: 2025-10-13

-- Option 1: Delete specific corrupted candidates (replace with actual IDs)
-- DELETE FROM work_experience WHERE candidate_id = '830fe63-15a6-4708-bec4-9a2e348b4662';
-- DELETE FROM education WHERE candidate_id = '830fe63-15a6-4708-bec4-9a2e348b4662';
-- DELETE FROM candidate_skills WHERE candidate_id = '830fe63-15a6-4708-bec4-9a2e348b4662';
-- DELETE FROM candidates WHERE id = '830fe63-15a6-4708-bec4-9a2e348b4662';

-- Option 2: Find and delete work experience with suspiciously long descriptions (> 2000 chars)
DELETE FROM work_experience 
WHERE LENGTH(description) > 2000;

-- Option 3: Find and delete education records with suspiciously long degree fields
DELETE FROM education 
WHERE LENGTH(degree) > 500;

-- Option 4: Truncate long descriptions in existing records (safer than delete)
UPDATE work_experience 
SET description = SUBSTRING(description, 1, 500) || '...'
WHERE LENGTH(description) > 2000;

-- Option 5: View candidates with corrupted data (for inspection)
SELECT 
    c.id,
    c.full_name,
    c.email,
    COUNT(DISTINCT we.id) as work_exp_count,
    COUNT(DISTINCT e.id) as education_count,
    MAX(LENGTH(we.description)) as max_desc_length,
    MAX(LENGTH(e.degree)) as max_degree_length
FROM candidates c
LEFT JOIN work_experience we ON c.id = we.candidate_id
LEFT JOIN education e ON c.id = e.candidate_id
GROUP BY c.id, c.full_name, c.email
HAVING MAX(LENGTH(we.description)) > 2000 OR MAX(LENGTH(e.degree)) > 500;

-- Option 6: Complete cleanup - delete all candidates with corrupted data
-- WARNING: This will delete candidates permanently!
-- DELETE FROM candidates 
-- WHERE id IN (
--     SELECT DISTINCT c.id
--     FROM candidates c
--     LEFT JOIN work_experience we ON c.id = we.candidate_id
--     LEFT JOIN education e ON c.id = e.candidate_id
--     WHERE LENGTH(we.description) > 2000 OR LENGTH(e.degree) > 500
-- );
