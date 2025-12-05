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
    # Add columns to checked_audio
    op.add_column('checked_audio', sa.Column('second_checker_id', sa.Integer(), sa.ForeignKey('admin_users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('checked_audio', sa.Column('second_check_result', sa.Boolean(), nullable=True))
    op.add_column('checked_audio', sa.Column('second_checked_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create the Enum type if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE adminrole AS ENUM ('admin', 'superadmin', 'checker');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Alter the existing role column from String to Enum
    op.execute("ALTER TABLE admin_users ALTER COLUMN role TYPE adminrole USING role::adminrole")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove columns from checked_audio
    op.drop_column('checked_audio', 'second_checked_at')
    op.drop_column('checked_audio', 'second_check_result')
    op.drop_column('checked_audio', 'second_checker_id')
    
    # Revert role column back to String
    op.alter_column('admin_users', 'role', type_=sa.String(), postgresql_using='role::text')
