from sqlalchemy import Table, Column, Integer, ForeignKey
from core.database import Base

# Many-to-Many relationship table between Candidates and Skills
candidate_skills = Table(
    'candidate_skills',
    Base.metadata,
    Column('candidate_id', Integer, ForeignKey('candidates.id', ondelete='CASCADE'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id', ondelete='CASCADE'), primary_key=True)
)
