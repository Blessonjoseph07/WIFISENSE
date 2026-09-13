import os
import shutil
import time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlmodel import Session
from app.core.database import get_session
from app.models.entities import User
from app.schemas.schemas import UserOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/me/photo", response_model=UserOut)
def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image."
        )
    
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    safe_filename = f"user_{current_user.id}_{int(time.time())}{ext}"
    target_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    current_user.photo_url = f"/uploads/{safe_filename}"
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return current_user

from typing import List
from sqlmodel import select
from app.models.entities import UserRole, Role, Organization
from app.schemas.schemas import PersonnelOut
from app.routers.auth import require_roles

@router.get("/personnel", response_model=List[PersonnelOut], dependencies=[Depends(require_roles(["system_admin", "organization_admin"]))])
def get_active_personnel(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    users = session.exec(select(User)).all()
    results = []
    for u in users:
        # Get roles
        user_roles = session.exec(select(UserRole).where(UserRole.user_id == u.id)).all()
        if not user_roles:
            continue
        
        # For simplicity, take the first role
        ur = user_roles[0]
        role = session.get(Role, ur.role_id)
        role_name = role.name if role else "Unknown"
        
        # Get organization
        org = session.get(Organization, ur.organization_id) if ur.organization_id else None
        
        scope_description = org.name if org else "Global Deployment Scope"
        if role_name == "system_admin":
            scope_description = "Global Deployment Scope"
        elif role_name == "caregiver":
            scope_description = f"{org.name if org else 'Facility'} - Patient Ward"
            
        permissions = ["View", "Edit"] if role_name in ["system_admin", "organization_admin"] else ["View"]
        
        results.append(PersonnelOut(
            id=u.id,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            is_active=u.is_active,
            role_name=role_name,
            scope_description=scope_description,
            permissions=permissions
        ))
    return results
