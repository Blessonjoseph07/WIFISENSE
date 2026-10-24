"""
Demo-account profile applied once, right after the demo data is first seeded.

  SEED_PROFILE=minimal   keep exactly one user per role (and one facility manager per context); delete every other user together
                         with everything that depends on them. Dependents are found from the models' own foreign keys, so the
                         same code works on SQLite and PostgreSQL.
  SEED_PASSWORD=<secret> give every remaining demo account this password instead of its well-known one. In production the
                         application refuses to seed demo accounts without it (see config.py).

Runs only when the database had no organizations before seeding, so a restart never changes an existing database.
"""
from sqlalchemy import delete, select as sa_select, update
from sqlmodel import Session, SQLModel, select

import app.models.entities  # noqa: F401  (registers every table on the metadata)
from app.core.config import settings
from app.core.security import hash_password
from app.models.entities import User

KEEP_EMAILS = {
    "blesson@wifisense.com",           # system admin
    "elizabeth@wifisense.com",         # facility manager, elder care
    "abhinand@wifisense.com",          # facility manager, corporate
    "mary@wifisense.com",              # caregiver
    "tomy@wifisense.com",              # corporate staff
    "mathew.varghese@wifisense.com",   # doctor
    "john@wifisense.com",              # family member
}


def _children(parent_table):
    out = []
    for table in SQLModel.metadata.tables.values():
        for fk in table.foreign_keys:
            if fk.column.table is parent_table:
                out.append((table, fk.parent, fk.column))
    return out


def _delete_rows(session: Session, table, ids) -> None:
    """Delete rows of `table` by primary key after deleting (required reference) or detaching (optional reference) dependents."""
    ids = list(ids)
    if not ids:
        return
    pk = list(table.primary_key.columns)
    if len(pk) != 1:
        raise RuntimeError(f"cannot cascade through {table.name}: no single-column primary key")
    pk_col = pk[0]
    for child, col, target in _children(table):
        if target.name != pk_col.name or child is table:
            raise RuntimeError(f"unsupported foreign key {child.name}.{col.name} -> {table.name}.{target.name}")
        if col.nullable:
            session.execute(update(child).where(col.in_(ids)).values({col.name: None}))
            continue
        child_pk = list(child.primary_key.columns)
        if len(child_pk) == 1:
            _delete_rows(session, child, [r[0] for r in session.execute(sa_select(child_pk[0]).where(col.in_(ids)))])
        else:
            session.execute(delete(child).where(col.in_(ids)))
    session.execute(delete(table).where(pk_col.in_(ids)))


def apply_demo_profile(session: Session) -> None:
    if settings.SEED_PROFILE == "minimal":
        drop = [u.id for u in session.exec(select(User)).all() if u.email not in KEEP_EMAILS]
        _delete_rows(session, User.__table__, drop)
        session.commit()
    if settings.SEED_PASSWORD:
        hashed = hash_password(settings.SEED_PASSWORD)
        for user in session.exec(select(User)).all():
            user.password_hash = hashed
            session.add(user)
        session.commit()


PAYER_EMAIL = "payer@wifisense.com"
PLACEHOLDER_HELPLINE = "+91 00000 00000"      # obviously not a real number: the facility sets its own (PATCH /organizations/{id}/contact)


def ensure_demo_extras(session: Session) -> None:
    """Idempotent, runs on every start when demo data is on. Creates, once, a family member whose Care Plan is NOT active, so the payment
    flow can be tried (the seeded family members all have a plan already), and gives the elder-care home a placeholder helpline if it has
    none. If the account is deleted or the helpline cleared later, nothing here puts them back unless the account is missing."""
    from datetime import datetime, timezone

    from app.core.seed import ROLE_MAPPING
    from app.models.entities import FamilyConnection, Organization, Resident, UserRole

    if session.exec(select(User).where(User.email == PAYER_EMAIL)).first():
        return
    mary = next((r for r in session.exec(select(Resident)).all() if r.first_name == "Mary" and r.last_name == "Joseph"), None)
    john = session.exec(select(User).where(User.email == "john@wifisense.com")).first()
    john_role = session.exec(select(UserRole).where(UserRole.user_id == john.id)).first() if john else None
    if not mary or not john_role:
        return                                               # the demo dataset is not there (for example a database without the seed)
    approver = session.exec(select(User).where(User.email == "elizabeth@wifisense.com")).first()
    user = User(email=PAYER_EMAIL, password_hash=hash_password(settings.SEED_PASSWORD or "payerpassword"),
                first_name="Meera", last_name="Joseph", resident_id=mary.id, is_active=True)
    session.add(user)
    session.commit()
    session.refresh(user)
    session.add(UserRole(user_id=user.id, role_id=ROLE_MAPPING["family_member"], organization_id=john_role.organization_id))
    session.add(FamilyConnection(resident_id=mary.id, family_user_id=user.id, relationship="Daughter", status="approved",
                                 approved_at=datetime.now(timezone.utc), approved_by=approver.id if approver else None))
    org = session.get(Organization, john_role.organization_id)
    if org and org.contact_phone is None:
        org.contact_phone = PLACEHOLDER_HELPLINE
        session.add(org)
    session.commit()
