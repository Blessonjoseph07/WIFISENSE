"""add_detection_windows_and_replay_evaluations

Revision ID: c4a8e2d1f9b3
Revises: b7e3a91c4d20
Create Date: 2026-10-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c4a8e2d1f9b3'
down_revision: Union[str, None] = 'b7e3a91c4d20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = sqlmodel.sql.sqltypes.AutoString


def upgrade() -> None:
    with op.batch_alter_table('raw_csi_telemetry', schema=None) as batch_op:
        batch_op.add_column(sa.Column('event_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_raw_csi_telemetry_event_id', ['event_id'], unique=False)

    op.create_table(
        'replay_evaluations',
        sa.Column('id', S(), nullable=False),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('sensing_events.id'), nullable=False),
        sa.Column('device_id', S(), sa.ForeignKey('devices.id'), nullable=False),
        sa.Column('dataset_name', S(), nullable=False),
        sa.Column('recorded_label', S(), nullable=False),
        sa.Column('created_by', S(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id'),
    )
    op.create_index('ix_replay_evaluations_event_id', 'replay_evaluations', ['event_id'])
    op.create_index('ix_replay_evaluations_device_id', 'replay_evaluations', ['device_id'])


def downgrade() -> None:
    op.drop_index('ix_replay_evaluations_device_id', table_name='replay_evaluations')
    op.drop_index('ix_replay_evaluations_event_id', table_name='replay_evaluations')
    op.drop_table('replay_evaluations')
    with op.batch_alter_table('raw_csi_telemetry', schema=None) as batch_op:
        batch_op.drop_index('ix_raw_csi_telemetry_event_id')
        batch_op.drop_column('event_id')
