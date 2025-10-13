"""add professional_summary to candidates

Revision ID: add_prof_summary_001
Revises: 002_resume_job_matches
Create Date: 2025-10-14 02:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_prof_summary_001'
down_revision = '002_resume_job_matches'
branch_labels = None
depends_on = None


def upgrade():
    # Add professional_summary column to candidates table
    op.add_column('candidates', sa.Column('professional_summary', sa.Text(), nullable=True))


def downgrade():
    # Remove professional_summary column from candidates table
    op.drop_column('candidates', 'professional_summary')
