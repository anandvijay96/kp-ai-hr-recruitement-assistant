"""add resume job matches table

Revision ID: 002_resume_job_matches
Revises: add_fulltext_search_support
Create Date: 2025-10-13 02:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_resume_job_matches'
down_revision = 'add_fulltext_search_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create resume_job_matches table
    op.create_table(
        'resume_job_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('match_score', sa.Integer, nullable=False),
        sa.Column('skill_score', sa.Integer, nullable=True),
        sa.Column('experience_score', sa.Integer, nullable=True),
        sa.Column('education_score', sa.Integer, nullable=True),
        sa.Column('matched_skills', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('missing_skills', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('match_details', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.CheckConstraint('match_score >= 0 AND match_score <= 100', name='check_match_score_range'),
        sa.CheckConstraint('skill_score >= 0 AND skill_score <= 100', name='check_skill_score_range'),
        sa.CheckConstraint('experience_score >= 0 AND experience_score <= 100', name='check_experience_score_range'),
        sa.CheckConstraint('education_score >= 0 AND education_score <= 100', name='check_education_score_range'),
        sa.UniqueConstraint('resume_id', 'job_id', name='unique_resume_job_match')
    )
    
    # Create indexes for performance
    op.create_index('idx_resume_job_matches_resume', 'resume_job_matches', ['resume_id'])
    op.create_index('idx_resume_job_matches_job', 'resume_job_matches', ['job_id'])
    op.create_index('idx_resume_job_matches_score', 'resume_job_matches', ['match_score'], postgresql_using='btree', postgresql_ops={'match_score': 'DESC'})
    op.create_index('idx_resume_job_matches_created', 'resume_job_matches', ['created_at'], postgresql_using='btree', postgresql_ops={'created_at': 'DESC'})


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_resume_job_matches_created', table_name='resume_job_matches')
    op.drop_index('idx_resume_job_matches_score', table_name='resume_job_matches')
    op.drop_index('idx_resume_job_matches_job', table_name='resume_job_matches')
    op.drop_index('idx_resume_job_matches_resume', table_name='resume_job_matches')
    
    # Drop table
    op.drop_table('resume_job_matches')
