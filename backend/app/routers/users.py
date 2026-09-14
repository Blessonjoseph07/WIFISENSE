import os
import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from sqlmodel import Session
from app.core.config import settings
from app.core.database import get_session
from app.models.entities import User
from app.schemas.schemas import UserOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])
uploads_router = APIRouter(prefix="/uploads", tags=["Users"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Raster formats only: SVG and HTML payloads are scriptable when served back
IMAGE_SIGNATURES = [
    (b"\xff\xd8\xff", ".jpg", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", ".png", "image/png"),
    (b"GIF87a", ".gif", "image/gif"),
    (b"GIF89a", ".gif", "image/gif"),
]
CHUNK_SIZE = 64 * 1024
PILLOW_FORMATS = {".jpg": "JPEG", ".png": "PNG", ".gif": "GIF", ".webp": "WEBP"}
MAX_IMAGE_PIXELS = 40_000_000
EXTENSION_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

def sniff_image_type(header: bytes):
    for signature, extension, media_type in IMAGE_SIGNATURES:
        if header.startswith(signature):
            return extension, media_type
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return ".webp", "image/webp"
    return None, None

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/me/photo", response_model=UserOut)
def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    header = file.file.read(512)
    extension, _media_type = sniff_image_type(header)
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a JPEG, PNG, GIF or WebP image."
        )

    safe_filename = f"user_{current_user.id}_{int(time.time())}_{uuid.uuid4().hex[:8]}{extension}"
    target_path = os.path.join(UPLOAD_DIR, safe_filename)

    too_large = HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"Image must be smaller than {settings.MAX_UPLOAD_BYTES} bytes."
    )

    written = len(header)
    if written > settings.MAX_UPLOAD_BYTES:
        raise too_large

    try:
        with open(target_path, "wb") as buffer:
            buffer.write(header)
            while True:
                chunk = file.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                written += len(chunk)
                if written > settings.MAX_UPLOAD_BYTES:
                    raise too_large
                buffer.write(chunk)
    except HTTPException:
        os.remove(target_path)
        raise

    try:
        with Image.open(target_path) as image:
            if image.format != PILLOW_FORMATS[extension]:
                raise UnidentifiedImageError(image.format or "unknown")
            width, height = image.size
            if width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Image must contain fewer than {MAX_IMAGE_PIXELS} pixels."
                )
            image.verify()
    except HTTPException:
        os.remove(target_path)
        raise
    except Exception:
        os.remove(target_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not a valid image."
        )

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

@uploads_router.get("/{filename}")
def get_uploaded_image(filename: str):
    extension = os.path.splitext(filename)[1].lower()
    if os.path.basename(filename) != filename or extension not in EXTENSION_MEDIA_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename.")

    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    return FileResponse(
        path,
        media_type=EXTENSION_MEDIA_TYPES[extension],
        headers={
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; sandbox",
        }
    )
