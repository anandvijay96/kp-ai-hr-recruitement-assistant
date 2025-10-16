-- Migration: Make uploaded_by nullable in resumes table
-- Date: 2025-10-16
-- Reason: Vetting flow doesn't have user context, needs to allow NULL

-- SQLite version
-- Note: SQLite doesn't support ALTER COLUMN directly, need to recreate table

-- For SQLite (development)
-- This will be handled by recreating the table with correct schema
-- Run: DROP TABLE IF EXISTS resumes; then restart app to recreate

-- For PostgreSQL (production)
ALTER TABLE resumes ALTER COLUMN uploaded_by DROP NOT NULL;

-- Verify
-- SELECT column_name, is_nullable FROM information_schema.columns 
-- WHERE table_name = 'resumes' AND column_name = 'uploaded_by';
