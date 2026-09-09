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
