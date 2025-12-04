"""add_indexes_for_performance

Revision ID: 33f3818c56b9
Revises: 92f8c83f7f05
Create Date: 2025-11-27 03:38:24.591512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33f3818c56b9'
down_revision: Union[str, Sequence[str], None] = '92f8c83f7f05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # received_audio indexes
    op.create_index('ix_received_audio_sentence_id', 'received_audio', ['sentence_id'])
    op.create_index('ix_received_audio_user_id', 'received_audio', ['user_id'])
    op.create_index('ix_received_audio_status', 'received_audio', ['status'])
    op.create_index('ix_received_audio_sentence_status_created', 'received_audio', ['sentence_id', 'status', 'created_at'])
    op.create_index('ix_received_audio_user_status', 'received_audio', ['user_id', 'status'])
    
    # checked_audio indexes
    op.create_index('ix_checked_audio_audio_id', 'checked_audio', ['audio_id'])
    op.create_index('ix_checked_audio_checked_by', 'checked_audio', ['checked_by'])
    op.create_index('ix_checked_audio_status', 'checked_audio', ['status'])
    op.create_index('ix_checked_audio_checked_by_status', 'checked_audio', ['checked_by', 'status'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop received_audio indexes
    op.drop_index('ix_received_audio_sentence_id', 'received_audio')
    op.drop_index('ix_received_audio_user_id', 'received_audio')
    op.drop_index('ix_received_audio_status', 'received_audio')
    op.drop_index('ix_received_audio_sentence_status_created', 'received_audio')
    op.drop_index('ix_received_audio_user_status', 'received_audio')
    
    # Drop checked_audio indexes
    op.drop_index('ix_checked_audio_audio_id', 'checked_audio')
    op.drop_index('ix_checked_audio_checked_by', 'checked_audio')
    op.drop_index('ix_checked_audio_status', 'checked_audio')
    op.drop_index('ix_checked_audio_checked_by_status', 'checked_audio')
