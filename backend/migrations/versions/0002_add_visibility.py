"""add visibility to choice_log

Revision ID: 0002_add_visibility
Revises: eaa029d9dac1
Create Date: 2026-06-24

Life standard (rev.4): every data table gets a visibility column
(public|private, default private), set at archiving time.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002_add_visibility'
down_revision: Union[str, None] = 'eaa029d9dac1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('choice_log',
        sa.Column('visibility', sa.String(length=10), nullable=False,
                  server_default='private'))
    op.create_index('ix_choice_log_visibility', 'choice_log', ['visibility'])


def downgrade() -> None:
    op.drop_index('ix_choice_log_visibility', table_name='choice_log')
    op.drop_column('choice_log', 'visibility')
