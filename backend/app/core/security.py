import bcrypt
from datetime import datetime, timedelta
from typing import Union, Any, Optional
from jose import jwt, JWTError
from app.core.config import settings

BCRYPT_MAX_BYTES = 72

def _encode_password(password: str) -> bytes:
    # bcrypt rejects inputs longer than 72 bytes
    return password.encode("utf-8")[:BCRYPT_MAX_BYTES]

def hash_password(password: str) -> str:
    # Use bcrypt directly as requested (no passlib)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(_encode_password(password), salt)
    return hashed.decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_encode_password(password), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(subject: Union[str, Any], role: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Validate that the token has not expired
        exp = decoded_token.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            return None
        return decoded_token
    except JWTError:
        return None
