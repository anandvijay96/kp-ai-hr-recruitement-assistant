#!/usr/bin/env python3
"""Quick fix: Extract names from resume filenames"""
from core.database import SessionLocal
from models.db import Candidate, Resume
import re

db = SessionLocal()

# Manual mapping based on your database output
name_mapping = {
    1: "Pranathi Pulavarthy",  # From Pulavarthy-Pranathi-Resume-4.11.pdf
    2: "Susmitha Addanki",      # From Susmitha_resume.pdf
    3: "Himanshu Jain",         # From Himanshu_Jain_PM_Resume (2).pdf
    4: "Deepak Venkatarao Pawar",  # From DeepakVenkatraoPawar.pdf
    5: "Atul Kumar",            # From Atul_Kumar_Sfmc.pdf
}

for cand_id, name in name_mapping.items():
    candidate = db.query(Candidate).filter(Candidate.id == cand_id).first()
    if candidate and candidate.full_name == 'Unknown':
        candidate.full_name = name
        print(f"✅ Updated Candidate {cand_id}: {name}")

db.commit()
print("\n✅ All names updated!")
db.close()
