"""add fulltext search support

Revision ID: add_fts_support
Revises: 
Create Date: 2025-10-08 23:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_fts_support'
down_revision = None  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Add full-text search support to candidates and resumes tables"""
    
    # Add tsvector column to candidates table
    op.add_column('candidates', 
                  sa.Column('search_vector', postgresql.TSVECTOR, nullable=True))
    
    # Add tsvector column to resumes table
    op.add_column('resumes', 
                  sa.Column('search_vector', postgresql.TSVECTOR, nullable=True))
    
    # Create GIN index on candidates.search_vector for fast full-text search
    op.create_index(
        'idx_candidates_search_vector',
        'candidates',
        ['search_vector'],
        postgresql_using='gin'
    )
    
    # Create GIN index on resumes.search_vector
    op.create_index(
        'idx_resumes_search_vector',
        'resumes',
        ['search_vector'],
        postgresql_using='gin'
    )
    
    # Create trigger function to auto-update search_vector on candidates
    op.execute("""
        CREATE OR REPLACE FUNCTION candidates_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := 
                setweight(to_tsvector('english', coalesce(NEW.full_name, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.email, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.phone_number, '')), 'C') ||
                setweight(to_tsvector('english', coalesce(NEW.location, '')), 'C') ||
                setweight(to_tsvector('english', coalesce(NEW.professional_summary, '')), 'D');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger on candidates table
    op.execute("""
        CREATE TRIGGER candidates_search_vector_trigger
        BEFORE INSERT OR UPDATE ON candidates
        FOR EACH ROW EXECUTE FUNCTION candidates_search_vector_update();
    """)
    
    # Create trigger function to auto-update search_vector on resumes
    op.execute("""
        CREATE OR REPLACE FUNCTION resumes_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := 
                setweight(to_tsvector('english', coalesce(NEW.file_name, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.raw_text, '')), 'C');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger on resumes table
    op.execute("""
        CREATE TRIGGER resumes_search_vector_trigger
        BEFORE INSERT OR UPDATE ON resumes
        FOR EACH ROW EXECUTE FUNCTION resumes_search_vector_update();
    """)
    
    # Update existing rows with search vectors
    op.execute("""
        UPDATE candidates SET 
            search_vector = 
                setweight(to_tsvector('english', coalesce(full_name, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(email, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(phone_number, '')), 'C') ||
                setweight(to_tsvector('english', coalesce(location, '')), 'C') ||
                setweight(to_tsvector('english', coalesce(professional_summary, '')), 'D');
    """)
    
    op.execute("""
        UPDATE resumes SET 
            search_vector = 
                setweight(to_tsvector('english', coalesce(file_name, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(raw_text, '')), 'C');
    """)


def downgrade():
    """Remove full-text search support"""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS candidates_search_vector_trigger ON candidates;")
    op.execute("DROP TRIGGER IF EXISTS resumes_search_vector_trigger ON resumes;")
    
    # Drop trigger functions
    op.execute("DROP FUNCTION IF EXISTS candidates_search_vector_update();")
    op.execute("DROP FUNCTION IF EXISTS resumes_search_vector_update();")
    
    # Drop indexes
    op.drop_index('idx_candidates_search_vector', table_name='candidates')
    op.drop_index('idx_resumes_search_vector', table_name='resumes')
    
    # Drop columns
    op.drop_column('candidates', 'search_vector')
    op.drop_column('resumes', 'search_vector')
