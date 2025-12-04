"""fake missing revision

Revision ID: cbb4de78e426
Revises: 14895829c099
Create Date: 2025-11-27 01:16:49.872001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbb4de78e426'
down_revision: Union[str, Sequence[str], None] = '14895829c099'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
