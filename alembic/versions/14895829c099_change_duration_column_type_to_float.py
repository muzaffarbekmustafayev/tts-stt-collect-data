"""change duration column type to float

Revision ID: 14895829c099
Revises: 53628905255b
Create Date: 2025-11-27 01:09:59.374693

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14895829c099'
down_revision: Union[str, Sequence[str], None] = '53628905255b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        'received_audio',
        'duration',
        type_=sa.DOUBLE_PRECISION(),   # yoki sa.FLOAT(), sa.REAL(), sa.DOUBLE_PRECISION
        existing_type=sa.Integer()  # oldingi turi
    )

def downgrade():
    op.alter_column(
        'received_audio',
        'duration',
        type_=sa.Integer(),
        existing_type=sa.DOUBLE_PRECISION()
    )