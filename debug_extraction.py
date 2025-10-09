#!/usr/bin/env python3
"""Debug name extraction"""
from core.database import SessionLocal
from models.db import Resume
from services.enhanced_resume_extractor import EnhancedResumeExtractor
import json

db = SessionLocal()
extractor = EnhancedResumeExtractor()

# Get first resume
resume = db.query(Resume).filter(Resume.id == 1).first()
print(f"Resume: {resume.file_name}")
print(f"Text length: {len(resume.raw_text)}")
print("\nFirst 500 chars of text:")
print("=" * 60)
print(resume.raw_text[:500])
print("=" * 60)

print("\nExtracting data...")
extracted = extractor.extract_all(resume.raw_text)

print("\nExtracted data:")
print(json.dumps(extracted, indent=2, default=str))

db.close()
