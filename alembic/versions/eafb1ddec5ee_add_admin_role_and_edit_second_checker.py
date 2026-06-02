"""add admin role and edit second_checker

Revision ID: eafb1ddec5ee
Revises: 33f3818c56b9
Create Date: 2025-12-04 23:17:32.381510

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eafb1ddec5ee'
down_revision: Union[str, Sequence[str], None] = '33f3818c56b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add columns to checked_audio (IF NOT EXISTS to handle already-applied columns)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE checked_audio ADD COLUMN second_checker_id INTEGER REFERENCES admin_users(id) ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_column THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE checked_audio ADD COLUMN second_check_result BOOLEAN;
        EXCEPTION WHEN duplicate_column THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE checked_audio ADD COLUMN second_checked_at TIMESTAMPTZ;
        EXCEPTION WHEN duplicate_column THEN null; END $$;
    """)
    
    # Create the Enum type if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE adminrole AS ENUM ('admin', 'superadmin', 'checker');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Drop the default value first (required when changing column type)
    op.execute("ALTER TABLE admin_users ALTER COLUMN role DROP DEFAULT")
    
    # Alter the existing role column from String to Enum
    op.execute("ALTER TABLE admin_users ALTER COLUMN role TYPE adminrole USING role::adminrole")
    
    # Set the default value again with the enum type
    op.execute("ALTER TABLE admin_users ALTER COLUMN role SET DEFAULT 'admin'::adminrole")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove columns from checked_audio
    op.drop_column('checked_audio', 'second_checked_at')
    op.drop_column('checked_audio', 'second_check_result')
    op.drop_column('checked_audio', 'second_checker_id')
    
    # Drop the default value first
    op.execute("ALTER TABLE admin_users ALTER COLUMN role DROP DEFAULT")
    
    # Revert role column back to String
    op.execute("ALTER TABLE admin_users ALTER COLUMN role TYPE VARCHAR USING role::text")
    
    # Set the default value again as String
    op.execute("ALTER TABLE admin_users ALTER COLUMN role SET DEFAULT 'admin'")
