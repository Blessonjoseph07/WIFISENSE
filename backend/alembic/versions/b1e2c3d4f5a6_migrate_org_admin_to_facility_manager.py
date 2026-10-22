"""migrate_org_admin_to_facility_manager

Revision ID: b1e2c3d4f5a6
Revises: e6c1a4b8d923
Create Date: 2026-10-23 18:00:00.000000

Converts every user_roles assignment with the organization_admin role ID to the facility_manager role ID.
Downgrade is a no-op as the organization_admin role is retired in Phase 1 and reserved for Phase 2.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1e2c3d4f5a6'
down_revision: Union[str, None] = 'e6c1a4b8d923'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # 1. Deduplicate if a user already has an identical scoped role assignment for facility_manager
    conn.execute(sa.text("""
        DELETE FROM user_roles
        WHERE role_id = (SELECT id FROM roles WHERE name = 'organization_admin')
        AND EXISTS (
            SELECT 1 FROM user_roles ur2
            WHERE ur2.user_id = user_roles.user_id
            AND ur2.role_id = (SELECT id FROM roles WHERE name = 'facility_manager')
            AND (ur2.organization_id = user_roles.organization_id OR (ur2.organization_id IS NULL AND user_roles.organization_id IS NULL))
            AND (ur2.building_id = user_roles.building_id OR (ur2.building_id IS NULL AND user_roles.building_id IS NULL))
            AND (ur2.room_id = user_roles.room_id OR (ur2.room_id IS NULL AND user_roles.room_id IS NULL))
        )
    """))
    # 2. Convert remaining user_roles assignments with organization_admin to facility_manager
    conn.execute(sa.text("""
        UPDATE user_roles
        SET role_id = (SELECT id FROM roles WHERE name = 'facility_manager')
        WHERE role_id = (SELECT id FROM roles WHERE name = 'organization_admin')
    """))


def downgrade() -> None:
    # Downgrade is intentionally a no-op as instructed for Phase 1 product scoping
    pass
