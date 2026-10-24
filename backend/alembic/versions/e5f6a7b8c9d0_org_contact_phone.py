"""org_contact_phone

Revision ID: e5f6a7b8c9d0
Revises: d3e4f5a6b7c8
Create Date: 2026-10-24 12:00:00.000000

The care home's own helpline, shown to approved family members. Nullable: nothing is invented for facilities that have not set one.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('organizations') as batch:
        batch.add_column(sa.Column('contact_phone', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('organizations') as batch:
        batch.drop_column('contact_phone')
