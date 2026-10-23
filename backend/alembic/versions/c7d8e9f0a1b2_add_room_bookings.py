"""add_room_bookings

Revision ID: c7d8e9f0a1b2
Revises: b1e2c3d4f5a6
Create Date: 2026-10-23 20:00:00.000000

Dated room reservations for corporate rooms (booking, cancellation, five-minute vacate reminder).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = 'b1e2c3d4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # A database that ran the older room-scheduling branch already has a table called room_bookings with a different
    # layout (title, booking_date, start_datetime, ...). Keep its rows under another name instead of failing.
    insp = sa.inspect(op.get_bind())
    if 'room_bookings' in insp.get_table_names():
        existing = {c['name'] for c in insp.get_columns('room_bookings')}
        if 'start_at' in existing:
            return  # already the current layout
        op.rename_table('room_bookings', 'room_bookings_legacy')
    op.create_table(
        'room_bookings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('room_id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=True),
        sa.Column('organizer_user_id', sa.String(), nullable=True),
        sa.Column('organizer_name', sa.String(), nullable=False),
        sa.Column('purpose', sa.String(), nullable=False),
        sa.Column('start_at', sa.DateTime(), nullable=False),
        sa.Column('end_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='BOOKED'),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_by', sa.String(), nullable=True),
        sa.Column('cancel_reason', sa.String(), nullable=True),
        sa.Column('reminder_issued_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_room_bookings_room_id', 'room_bookings', ['room_id'])
    op.create_index('ix_room_bookings_organization_id', 'room_bookings', ['organization_id'])
    op.create_index('ix_room_bookings_start_at', 'room_bookings', ['start_at'])
    op.create_index('ix_room_bookings_status', 'room_bookings', ['status'])


def downgrade() -> None:
    op.drop_index('ix_room_bookings_status', table_name='room_bookings')
    op.drop_index('ix_room_bookings_start_at', table_name='room_bookings')
    op.drop_index('ix_room_bookings_organization_id', table_name='room_bookings')
    op.drop_index('ix_room_bookings_room_id', table_name='room_bookings')
    op.drop_table('room_bookings')
    if 'room_bookings_legacy' in sa.inspect(op.get_bind()).get_table_names():
        op.rename_table('room_bookings_legacy', 'room_bookings')
