"""migrate_legacy_emergency_contact_users_to_family_member

Revision ID: f2081373ae80
Revises: 9a5fcc6e884f
Create Date: 2026-09-15 07:29:15.129258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2081373ae80'
down_revision: Union[str, None] = '9a5fcc6e884f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Ensure role 7 ("family_member") exists in roles table
    conn.execute(sa.text("INSERT OR IGNORE INTO roles (id, name) VALUES (7, 'family_member')"))
    # Migrate all user_roles assignments from role_id 6 (legacy emergency_contact login) to role_id 7 (family_member)
    conn.execute(sa.text("UPDATE user_roles SET role_id = 7 WHERE role_id = 6"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE user_roles SET role_id = 6 WHERE role_id = 7"))

