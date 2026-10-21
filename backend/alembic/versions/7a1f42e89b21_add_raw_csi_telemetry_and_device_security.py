"""add_raw_csi_telemetry_and_device_security

Revision ID: 7a1f42e89b21
Revises: f2081373ae80
Create Date: 2026-10-21 22:55:00.000000

"""
import secrets
import hashlib
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '7a1f42e89b21'
down_revision: Union[str, None] = 'f2081373ae80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add security and source columns to devices table
    with op.batch_alter_table('devices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('hardware_token_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.add_column(sa.Column('allowed_source', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='live'))
        batch_op.create_index('ix_devices_hardware_token_hash', ['hardware_token_hash'], unique=False)

    # 2. Rotate any existing seed/dev devices: do NOT hash old plaintext tokens, generate new high-entropy hashes and clear plaintext
    conn = op.get_bind()
    devices = conn.execute(sa.text("SELECT id FROM devices")).fetchall()
    for row in devices:
        dev_id = row[0]
        raw_token = f"TK-ESP32-{secrets.token_urlsafe(32)}"
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        conn.execute(
            sa.text("UPDATE devices SET hardware_token = NULL, hardware_token_hash = :th, allowed_source = 'live' WHERE id = :did"),
            {"th": token_hash, "did": dev_id}
        )

    # 3. Create raw_csi_telemetry table
    op.create_table(
        'raw_csi_telemetry',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column('device_id', sqlmodel.sql.sqltypes.AutoString(), sa.ForeignKey('devices.id'), nullable=False),
        sa.Column('room_id', sqlmodel.sql.sqltypes.AutoString(), sa.ForeignKey('rooms.id'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=True),
        sa.Column('rssi', sa.Integer(), nullable=False),
        sa.Column('noise_floor', sa.Integer(), nullable=True),
        sa.Column('subcarrier_count', sa.Integer(), nullable=False, server_default='56'),
        sa.Column('bandwidth_mhz', sa.Integer(), nullable=True, server_default='20'),
        sa.Column('channel', sa.Integer(), nullable=True),
        sa.Column('csi_data', sa.JSON(), nullable=False),
        sa.Column('provenance', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='live'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('raw_csi_telemetry', schema=None) as batch_op:
        batch_op.create_index('ix_raw_csi_telemetry_device_id', ['device_id'], unique=False)
        batch_op.create_index('ix_raw_csi_telemetry_room_id', ['room_id'], unique=False)
        batch_op.create_index('ix_raw_csi_telemetry_timestamp', ['timestamp'], unique=False)
        batch_op.create_index('ix_raw_csi_telemetry_provenance', ['provenance'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('raw_csi_telemetry', schema=None) as batch_op:
        batch_op.drop_index('ix_raw_csi_telemetry_provenance')
        batch_op.drop_index('ix_raw_csi_telemetry_timestamp')
        batch_op.drop_index('ix_raw_csi_telemetry_room_id')
        batch_op.drop_index('ix_raw_csi_telemetry_device_id')
    op.drop_table('raw_csi_telemetry')

    with op.batch_alter_table('devices', schema=None) as batch_op:
        batch_op.drop_index('ix_devices_hardware_token_hash')
        batch_op.drop_column('allowed_source')
        batch_op.drop_column('hardware_token_hash')
