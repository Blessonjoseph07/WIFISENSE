"""add_appointments_and_medication_logs

Revision ID: 8c3d5e1a7b44
Revises: 7a1f42e89b21
Create Date: 2026-10-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '8c3d5e1a7b44'
down_revision: Union[str, None] = '7a1f42e89b21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'appointments',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('resident_id', sqlmodel.sql.sqltypes.AutoString(), sa.ForeignKey('residents.id'), nullable=False),
        sa.Column('doctor_id', sqlmodel.sql.sqltypes.AutoString(), sa.ForeignKey('doctors.id'), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('purpose', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='SCHEDULED'),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('created_by', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_appointments_resident_id', 'appointments', ['resident_id'])
    op.create_index('ix_appointments_scheduled_at', 'appointments', ['scheduled_at'])

    op.create_table(
        'medication_logs',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('resident_id', sqlmodel.sql.sqltypes.AutoString(), sa.ForeignKey('residents.id'), nullable=False),
        sa.Column('prescription_id', sqlmodel.sql.sqltypes.AutoString(), sa.ForeignKey('prescriptions.id'), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('administered_at', sa.DateTime(), nullable=False),
        sa.Column('administered_by', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_medication_logs_resident_id', 'medication_logs', ['resident_id'])
    op.create_index('ix_medication_logs_prescription_id', 'medication_logs', ['prescription_id'])


def downgrade() -> None:
    op.drop_index('ix_medication_logs_prescription_id', table_name='medication_logs')
    op.drop_index('ix_medication_logs_resident_id', table_name='medication_logs')
    op.drop_table('medication_logs')
    op.drop_index('ix_appointments_scheduled_at', table_name='appointments')
    op.drop_index('ix_appointments_resident_id', table_name='appointments')
    op.drop_table('appointments')
