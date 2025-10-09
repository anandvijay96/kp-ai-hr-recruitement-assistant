#!/usr/bin/env python3
"""Quick script to check database contents"""
from core.database import SessionLocal
from models.db import Candidate, Resume

db = SessionLocal()

print("=" * 60)
print("CANDIDATES:")
print("=" * 60)
candidates = db.query(Candidate).all()
for c in candidates:
    print(f"ID: {c.id}, Name: {c.full_name}, Email: {c.email}")

print("\n" + "=" * 60)
print("RESUMES:")
print("=" * 60)
resumes = db.query(Resume).all()
for r in resumes:
    print(f"ID: {r.id}, File: {r.file_name}, Status: {r.upload_status}, Candidate ID: {r.candidate_id}")
    if r.extracted_data:
        print(f"  -> Extracted Name: {r.extracted_data.get('name')}, Email: {r.extracted_data.get('email')}")

db.close()
