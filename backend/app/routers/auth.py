from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.models.entities import User, UserRole, Role, Organization, Building, Room
from app.schemas.schemas import UserRegister, UserLogin, Token, UserOut, RoleAssignment

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

ROLE_MAPPING = {
    "system_admin": 1,
    "organization_admin": 2,
    "facility_manager": 3,
    "caregiver": 4,
    "corporate_staff": 5,
    "emergency_contact": 6
}

DEFAULT_REGISTRATION_ROLE = "emergency_contact"

ROLE_NAMES = {
    1: "system_admin",
    2: "organization_admin",
    3: "facility_manager",
    4: "caregiver",
    5: "corporate_staff",
    6: "emergency_contact"
}

def seed_roles_if_empty(session: Session):
    for name, role_id in ROLE_MAPPING.items():
        existing = session.get(Role, role_id)
        if not existing:
            new_role = Role(id=role_id, name=name)
            session.add(new_role)
    session.commit()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, session: Session = Depends(get_session)):
    """Self-service registration. Always creates an unprivileged account;
    privileged roles and scopes are granted by an administrator via /auth/assign-role."""
    seed_roles_if_empty(session)

    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    hashed_pwd = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        password_hash=hashed_pwd,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    user_role = UserRole(
        user_id=user.id,
        role_id=ROLE_MAPPING[DEFAULT_REGISTRATION_ROLE]
    )
    session.add(user_role)
    session.commit()
    session.refresh(user)

    return user

def get_user_role_and_context(user: User, session: Session):
    # Fetch roles deterministically ordered by created_at
    role_statement = select(UserRole).where(UserRole.user_id == user.id).order_by(UserRole.created_at)
    user_roles = session.exec(role_statement).all()

    if not user_roles:
        return "emergency_contact", "ELDER_CARE", False

    # Check if system_admin
    for ur in user_roles:
        if ur.role_id == 1:
            return "system_admin", "SYSTEM", True

    # Check for conflicting org types across assigned roles
    org_types = set()
    for ur in user_roles:
        if ur.organization_id:
            org = session.get(Organization, ur.organization_id)
            if org and org.type:
                org_types.add(org.type)
    
    if len(org_types) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User holds conflicting assignments across both ELDER_CARE and CORPORATE organizations."
        )

    # Pin role and application_context to the single deterministic UserRole row
    primary_role_map = user_roles[0]
    role_name = ROLE_NAMES.get(primary_role_map.role_id, "emergency_contact")

    if primary_role_map.organization_id:
        org = session.get(Organization, primary_role_map.organization_id)
        app_context = org.type if org else ("CORPORATE" if role_name == "corporate_staff" else "ELDER_CARE")
    else:
        app_context = "CORPORATE" if role_name == "corporate_staff" else "ELDER_CARE"

    return role_name, app_context, False

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, session: Session = Depends(get_session)):
    seed_roles_if_empty(session)

    # Fetch user
    statement = select(User).where(User.email == login_data.email)
    user = session.exec(statement).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated."
        )

    # Fetch user's role and application context deterministically
    role_name, app_context, is_sysadmin = get_user_role_and_context(user, session)

    # Generate JWT
    token = create_access_token(subject=user.id, role=role_name)
    return Token(
        access_token=token,
        token_type="bearer",
        role=role_name,
        application_context=app_context,
        is_system_admin=is_sysadmin,
        user=UserOut.from_orm(user)
    )

@router.get("/me", response_model=Token)
def get_auth_me(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
):
    current_user = get_current_user(token=token, session=session)
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    return Token(
        access_token=token,
        token_type="bearer",
        role=role_name,
        application_context=app_context,
        is_system_admin=is_sysadmin,
        user=UserOut.from_orm(current_user)
    )

# Dependency to fetch the active authenticated user
def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials."
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload."
        )
        
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )
    return user

# Helper to verify role limits. The role is resolved from the database on every
# request so revoked or changed assignments take effect immediately.
def require_roles(allowed_roles: list):
    def dependency(
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
    ):
        role, _app_context, _is_sysadmin = get_user_role_and_context(current_user, session)
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource."
            )
        return role
    return dependency

def get_user_scopes(user: User):
    scopes = {
        "is_system_admin": False,
        "organization_ids": set(),
        "building_ids": set(),
        "room_ids": set()
    }
    for role in user.roles:
        if role.role_id == 1:
            scopes["is_system_admin"] = True
            return scopes
        if role.organization_id:
            scopes["organization_ids"].add(role.organization_id)
        if role.building_id:
            scopes["building_ids"].add(role.building_id)
        if role.room_id:
            scopes["room_ids"].add(role.room_id)
    return scopes

@router.post("/assign-role", response_model=UserOut, dependencies=[Depends(require_roles(["system_admin"]))])
def assign_role(
    assignment: RoleAssignment,
    session: Session = Depends(get_session)
):
    seed_roles_if_empty(session)

    if assignment.role not in ROLE_MAPPING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Supported roles: {list(ROLE_MAPPING.keys())}"
        )

    target_user = session.get(User, assignment.user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if assignment.organization_id and not session.get(Organization, assignment.organization_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    if assignment.building_id and not session.get(Building, assignment.building_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")
    if assignment.room_id and not session.get(Room, assignment.room_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    existing_roles = session.exec(select(UserRole).where(UserRole.user_id == target_user.id)).all()
    for existing in existing_roles:
        session.delete(existing)

    session.add(UserRole(
        user_id=target_user.id,
        role_id=ROLE_MAPPING[assignment.role],
        organization_id=assignment.organization_id,
        building_id=assignment.building_id,
        room_id=assignment.room_id
    ))
    session.commit()
    session.refresh(target_user)
    return target_user
