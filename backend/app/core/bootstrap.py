from sqlmodel import Session, select
from app.core.config import settings
from app.core.security import hash_password
from app.models.entities import User, UserRole
from app.routers.auth import seed_roles_if_empty

SYSTEM_ADMIN_ROLE_ID = 1


def bootstrap_system_admin(session: Session) -> None:
    """Create the first system administrator from the environment.

    Without this a fresh install has no privileged account: self-registration only
    ever grants emergency_contact and /auth/assign-role requires an administrator.
    Runs only while no system administrator exists.
    """
    if not settings.BOOTSTRAP_ADMIN_EMAIL or not settings.BOOTSTRAP_ADMIN_PASSWORD:
        return

    seed_roles_if_empty(session)

    existing_admin = session.exec(
        select(UserRole).where(UserRole.role_id == SYSTEM_ADMIN_ROLE_ID)
    ).first()
    if existing_admin:
        return

    user = session.exec(
        select(User).where(User.email == settings.BOOTSTRAP_ADMIN_EMAIL)
    ).first()
    if not user:
        user = User(
            email=settings.BOOTSTRAP_ADMIN_EMAIL,
            password_hash=hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD),
            first_name="System",
            last_name="Administrator",
            is_active=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)

    session.add(UserRole(user_id=user.id, role_id=SYSTEM_ADMIN_ROLE_ID))
    session.commit()
