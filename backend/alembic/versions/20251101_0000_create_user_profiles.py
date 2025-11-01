"""Create user_profiles table

Revision ID: 20251101_0000
Revises: 20251019_1200_add_github_scraping_fields
Create Date: 2025-11-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251101_0000'
down_revision = 'add_papers_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_profiles table with Google Auth integration."""

    # Create user_profiles table
    op.create_table(
        'user_profiles',

        # Primary key (Google Auth UUID)
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            primary_key=True,
            comment='User UUID from Google Auth (Supabase auth.users.id)'
        ),

        # User information
        sa.Column(
            'email',
            sa.String(255),
            nullable=False,
            unique=True,
            comment='User email address from Google Auth'
        ),
        sa.Column(
            'display_name',
            sa.String(200),
            nullable=True,
            comment='User display name'
        ),
        sa.Column(
            'avatar_url',
            sa.String(500),
            nullable=True,
            comment='User avatar/profile picture URL'
        ),

        # Preferences
        sa.Column(
            'preferences',
            postgresql.JSONB,
            nullable=True,
            server_default='{}',
            comment='User preferences and settings'
        ),

        # Timestamps
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('NOW()'),
            comment='Profile creation timestamp'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('NOW()'),
            comment='Last profile update timestamp'
        ),
        sa.Column(
            'last_login_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Last login timestamp'
        ),
    )

    # Create indexes for performance
    op.create_index(
        'idx_user_profiles_email',
        'user_profiles',
        ['email'],
        unique=True
    )
    op.create_index(
        'idx_user_profiles_created_at',
        'user_profiles',
        ['created_at']
    )

    # Add user_id foreign key to crawler_jobs table
    op.add_column(
        'crawler_jobs',
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Owner of this crawler job (NULL for system jobs)'
        )
    )

    # Create foreign key constraint
    op.create_foreign_key(
        'fk_crawler_jobs_user_id',
        'crawler_jobs',
        'user_profiles',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Create index on user_id for crawler_jobs
    op.create_index(
        'idx_crawler_jobs_user_id',
        'crawler_jobs',
        ['user_id']
    )

    # Create index on user_id + status for active job queries
    op.create_index(
        'idx_crawler_jobs_user_status',
        'crawler_jobs',
        ['user_id', 'status']
    )

    # Add foreign key constraint to topics table user_id (already exists in schema)
    # This ensures custom topics are linked to user_profiles
    op.create_foreign_key(
        'fk_topics_user_id',
        'topics',
        'user_profiles',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Create index on topics.user_id
    op.create_index(
        'idx_topics_user_id',
        'topics',
        ['user_id']
    )


def downgrade() -> None:
    """Remove user_profiles table and related changes."""

    # Drop indexes from topics
    op.drop_index('idx_topics_user_id', table_name='topics')

    # Drop foreign key from topics
    op.drop_constraint('fk_topics_user_id', 'topics', type_='foreignkey')

    # Drop indexes from crawler_jobs
    op.drop_index('idx_crawler_jobs_user_status', table_name='crawler_jobs')
    op.drop_index('idx_crawler_jobs_user_id', table_name='crawler_jobs')

    # Drop foreign key from crawler_jobs
    op.drop_constraint('fk_crawler_jobs_user_id', 'crawler_jobs', type_='foreignkey')

    # Drop user_id column from crawler_jobs
    op.drop_column('crawler_jobs', 'user_id')

    # Drop indexes from user_profiles
    op.drop_index('idx_user_profiles_created_at', table_name='user_profiles')
    op.drop_index('idx_user_profiles_email', table_name='user_profiles')

    # Drop user_profiles table
    op.drop_table('user_profiles')
