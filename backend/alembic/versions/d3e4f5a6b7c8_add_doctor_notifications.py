"""add_doctor_notifications

Revision ID: d3e4f5a6b7c8
Revises: c7d8e9f0a1b2
Create Date: 2026-10-23 23:00:00.000000

Messages from care staff to approved, assigned doctors (fall notifications).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if 'doctor_notifications' in sa.inspect(op.get_bind()).get_table_names():
        return  # created earlier by a database that was built from the models directly
    op.create_table(
        'doctor_notifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('doctor_profile_id', sa.String(), nullable=False),
        sa.Column('resident_id', sa.String(), nullable=False),
        sa.Column('alert_id', sa.String(), nullable=True),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['doctor_profile_id'], ['doctor_profiles.id']),
        sa.ForeignKeyConstraint(['resident_id'], ['residents.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_doctor_notifications_doctor_profile_id', 'doctor_notifications', ['doctor_profile_id'])
    op.create_index('ix_doctor_notifications_resident_id', 'doctor_notifications', ['resident_id'])
    op.create_index('ix_doctor_notifications_alert_id', 'doctor_notifications', ['alert_id'])


def downgrade() -> None:
    op.drop_index('ix_doctor_notifications_alert_id', table_name='doctor_notifications')
    op.drop_index('ix_doctor_notifications_resident_id', table_name='doctor_notifications')
    op.drop_index('ix_doctor_notifications_doctor_profile_id', table_name='doctor_notifications')
    op.drop_table('doctor_notifications')
