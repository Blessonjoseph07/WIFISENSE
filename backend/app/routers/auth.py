from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.models.entities import User, UserRole, Role, Organization, Building, Room
from app.schemas.schemas import UserRegister, UserLogin, Token, UserOut

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
    seed_roles_if_empty(session)
    
    # Check if user already exists
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Validate role
    if user_data.role not in ROLE_MAPPING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Supported roles: {list(ROLE_MAPPING.keys())}"
        )

    # Validate parent scopes if provided
    if user_data.organization_id:
        org = session.get(Organization, user_data.organization_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    if user_data.building_id:
        bld = session.get(Building, user_data.building_id)
        if not bld:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")
    if user_data.room_id:
        rm = session.get(Room, user_data.room_id)
        if not rm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    # Hash password and create user
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

    # Create UserRole mapping
    user_role = UserRole(
        user_id=user.id,
        role_id=ROLE_MAPPING[user_data.role],
        organization_id=user_data.organization_id,
        building_id=user_data.building_id,
        room_id=user_data.room_id
    )
    session.add(user_role)
    session.commit()
    session.refresh(user)

    return user

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

    # Fetch user's role
    role_statement = select(UserRole).where(UserRole.user_id == user.id)
    user_role_map = session.exec(role_statement).first()
    role_name = "emergency_contact"  # default fallback
    if user_role_map:
        role_name = ROLE_NAMES.get(user_role_map.role_id, "emergency_contact")

    # Generate JWT
    token = create_access_token(subject=user.id, role=role_name)
    return Token(
        access_token=token,
        token_type="bearer",
        role=role_name,
        user=UserOut.from_orm(user)
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
    return user

# Helper to verify role limits
def require_roles(allowed_roles: list):
    def dependency(token: str = Depends(oauth2_scheme)):
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials."
            )
        role = payload.get("role")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource."
            )
        return role
    return dependency
