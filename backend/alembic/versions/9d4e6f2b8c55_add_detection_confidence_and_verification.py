"""add_detection_confidence_and_verification

Revision ID: 9d4e6f2b8c55
Revises: 8c3d5e1a7b44
Create Date: 2026-10-22 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '9d4e6f2b8c55'
down_revision: Union[str, None] = '8c3d5e1a7b44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('sensing_events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='simulated'))

    with op.batch_alter_table('alerts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='simulated'))
        batch_op.add_column(sa.Column('device_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.add_column(sa.Column('confidence', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('signal_quality', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('verification_status', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='UNVERIFIED'))
        batch_op.add_column(sa.Column('verified_by', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.add_column(sa.Column('verified_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('verification_note', sqlmodel.sql.sqltypes.AutoString(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('alerts', schema=None) as batch_op:
        batch_op.drop_column('verification_note')
        batch_op.drop_column('verified_at')
        batch_op.drop_column('verified_by')
        batch_op.drop_column('verification_status')
        batch_op.drop_column('signal_quality')
        batch_op.drop_column('confidence')
        batch_op.drop_column('device_id')
        batch_op.drop_column('source')

    with op.batch_alter_table('sensing_events', schema=None) as batch_op:
        batch_op.drop_column('source')
