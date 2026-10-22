"""scope_audit_logs_by_organization

Revision ID: d5b9f3a7c612
Revises: c4a8e2d1f9b3
Create Date: 2026-10-23 12:00:00.000000

Adds audit_logs.organization_id and attributes existing rows where exactly one organization can be named
(the acting user's single organization, a doctor's organization, or details.organization_id). Everything else stays NULL
and is therefore visible to the system administrator only.
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'd5b9f3a7c612'
down_revision: Union[str, None] = 'c4a8e2d1f9b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('audit_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organization_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.create_index('ix_audit_logs_organization_id', ['organization_id'], unique=False)

    conn = op.get_bind()
    orgs_by_user = {}
    for user_id, org_id in conn.execute(sa.text(
            "SELECT user_id, organization_id FROM user_roles WHERE organization_id IS NOT NULL")).fetchall():
        orgs_by_user.setdefault(user_id, set()).add(org_id)
    doctor_org = {u: o for u, o in conn.execute(sa.text("SELECT user_id, organization_id FROM doctor_profiles")).fetchall()}
    user_by_email = {e: i for i, e in conn.execute(sa.text("SELECT id, email FROM users")).fetchall()}

    rows = conn.execute(sa.text("SELECT id, who_user_id, who_email, details FROM audit_logs")).fetchall()
    for log_id, who_user_id, who_email, details in rows:
        user_id = who_user_id or user_by_email.get(who_email)
        org = None
        if user_id:
            orgs = orgs_by_user.get(user_id, set())
            if len(orgs) == 1:
                org = next(iter(orgs))
            elif not orgs:
                org = doctor_org.get(user_id)
        if org is None and details:
            try:
                d = json.loads(details) if isinstance(details, str) else details
                cand = d.get("organization_id") if isinstance(d, dict) else None
                org = cand if isinstance(cand, str) and cand else None
            except (ValueError, TypeError):
                org = None
        if org:
            conn.execute(sa.text("UPDATE audit_logs SET organization_id = :o WHERE id = :i"), {"o": org, "i": log_id})


def downgrade() -> None:
    with op.batch_alter_table('audit_logs', schema=None) as batch_op:
        batch_op.drop_index('ix_audit_logs_organization_id')
        batch_op.drop_column('organization_id')
