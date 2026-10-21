"""add_doctor_workflow

Revision ID: b7e3a91c4d20
Revises: 9d4e6f2b8c55
Create Date: 2026-10-22 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b7e3a91c4d20'
down_revision: Union[str, None] = '9d4e6f2b8c55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = sqlmodel.sql.sqltypes.AutoString


def upgrade() -> None:
    op.create_table(
        'doctor_profiles',
        sa.Column('id', S(), nullable=False),
        sa.Column('user_id', S(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('organization_id', S(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('clinic_name', S(), nullable=False),
        sa.Column('specialty', S(), nullable=False),
        sa.Column('license_number', S(), nullable=False),
        sa.Column('status', S(), nullable=False, server_default='PENDING'),
        sa.Column('reviewed_by', S(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_note', S(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_doctor_profiles_organization_id', 'doctor_profiles', ['organization_id'])

    op.create_table(
        'doctor_assignments',
        sa.Column('id', S(), nullable=False),
        sa.Column('doctor_profile_id', S(), sa.ForeignKey('doctor_profiles.id'), nullable=False),
        sa.Column('resident_id', S(), sa.ForeignKey('residents.id'), nullable=False),
        sa.Column('status', S(), nullable=False, server_default='ACTIVE'),
        sa.Column('assigned_by', S(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_by', S(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_doctor_assignments_doctor_profile_id', 'doctor_assignments', ['doctor_profile_id'])
    op.create_index('ix_doctor_assignments_resident_id', 'doctor_assignments', ['resident_id'])

    op.create_table(
        'consultations',
        sa.Column('id', S(), nullable=False),
        sa.Column('resident_id', S(), sa.ForeignKey('residents.id'), nullable=False),
        sa.Column('doctor_profile_id', S(), sa.ForeignKey('doctor_profiles.id'), nullable=False),
        sa.Column('consulted_at', sa.DateTime(), nullable=False),
        sa.Column('reason', S(), nullable=False),
        sa.Column('notes', S(), nullable=True),
        sa.Column('follow_up_date', sa.DateTime(), nullable=True),
        sa.Column('follow_up_done', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_consultations_resident_id', 'consultations', ['resident_id'])
    op.create_index('ix_consultations_doctor_profile_id', 'consultations', ['doctor_profile_id'])

    op.create_table(
        'allergies',
        sa.Column('id', S(), nullable=False),
        sa.Column('resident_id', S(), sa.ForeignKey('residents.id'), nullable=False),
        sa.Column('allergen', S(), nullable=False),
        sa.Column('reaction', S(), nullable=True),
        sa.Column('severity', S(), nullable=False, server_default='MODERATE'),
        sa.Column('recorded_by', S(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_allergies_resident_id', 'allergies', ['resident_id'])


def downgrade() -> None:
    op.drop_index('ix_allergies_resident_id', table_name='allergies')
    op.drop_table('allergies')
    op.drop_index('ix_consultations_doctor_profile_id', table_name='consultations')
    op.drop_index('ix_consultations_resident_id', table_name='consultations')
    op.drop_table('consultations')
    op.drop_index('ix_doctor_assignments_resident_id', table_name='doctor_assignments')
    op.drop_index('ix_doctor_assignments_doctor_profile_id', table_name='doctor_assignments')
    op.drop_table('doctor_assignments')
    op.drop_index('ix_doctor_profiles_organization_id', table_name='doctor_profiles')
    op.drop_table('doctor_profiles')
