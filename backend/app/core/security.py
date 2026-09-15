import uuid
import secrets
import hashlib
import bcrypt
from datetime import datetime, timedelta
from typing import Union, Any, Optional, Tuple, Dict
from jose import jwt, JWTError
from sqlmodel import Session, select
from app.core.config import settings
from app.models.entities import RefreshToken, TokenRevocation, User

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

def hash_token(raw_token: str) -> str:
    """Returns SHA-256 hex digest of a token string for safe database lookup."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

def create_access_token(subject: Union[str, Any], role: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    jti = str(uuid.uuid4())
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role,
        "jti": jti,
        "iat": datetime.utcnow()
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def is_token_revoked(token: str, session: Session) -> bool:
    """Checks whether the access token has been revoked server-side."""
    try:
        token_hash = hash_token(token)
        statement = select(TokenRevocation).where(TokenRevocation.token_identifier == token_hash)
        revoked = session.exec(statement).first()
        if revoked:
            return True

        # Also check by jti if present
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
        jti = payload.get("jti")
        if jti:
            jti_statement = select(TokenRevocation).where(TokenRevocation.token_identifier == jti)
            if session.exec(jti_statement).first():
                return True
        return False
    except Exception:
        return False

def decode_access_token(token: str, session: Optional[Session] = None) -> Optional[dict]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Validate that the token has not expired
        exp = decoded_token.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            return None

        # Check server-side revocation list if database session is provided
        if session and is_token_revoked(token, session):
            return None

        return decoded_token
    except JWTError:
        return None

def create_refresh_token(user_id: str, session: Session) -> Tuple[str, RefreshToken]:
    """Generates a cryptographically secure refresh token and stores its hash in the database."""
    raw_token = secrets.token_urlsafe(64)
    token_hash = hash_token(raw_token)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_token = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        created_at=datetime.utcnow()
    )
    session.add(db_token)
    session.commit()
    session.refresh(db_token)
    return raw_token, db_token

def verify_and_rotate_refresh_token(raw_refresh_token: str, session: Session) -> Tuple[User, str, RefreshToken]:
    """
    Validates a refresh token, revokes it (single-use rotation), and issues a new refresh token.
    Detects refresh token reuse attacks: if an already-revoked token is used, invalidates all tokens for the user.
    """
    token_hash = hash_token(raw_refresh_token)
    statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    db_token = session.exec(statement).first()

    if not db_token:
        raise ValueError("Invalid refresh token.")

    # Refresh Token Reuse Detection
    if db_token.revoked_at is not None:
        # Compromised token reused! Revoke all tokens for this user immediately
        revoke_all_user_tokens(db_token.user_id, session, reason="refresh_token_reuse_detected")
        raise ValueError("Refresh token reuse detected. All sessions invalidated for security.")

    if db_token.expires_at < datetime.utcnow():
        raise ValueError("Refresh token has expired. Please log in again.")

    user = session.get(User, db_token.user_id)
    if not user or not user.is_active:
        raise ValueError("User account is inactive or no longer exists.")

    # Generate new refresh token
    new_raw_token = secrets.token_urlsafe(64)
    new_token_hash = hash_token(new_raw_token)
    new_expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_db_token = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=new_token_hash,
        expires_at=new_expires_at,
        created_at=datetime.utcnow()
    )
    session.add(new_db_token)
    session.flush()

    # Invalidate the old refresh token and link replacement
    db_token.revoked_at = datetime.utcnow()
    db_token.replaced_by_token_id = new_db_token.id
    session.add(db_token)

    session.commit()
    session.refresh(new_db_token)
    return user, new_raw_token, new_db_token

def revoke_access_token(token: str, session: Session, reason: str = "logout"):
    """Adds access token hash to server-side revocation blacklist."""
    try:
        token_hash = hash_token(token)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
        exp = payload.get("exp")
        user_id = payload.get("sub")
        expires_at = datetime.utcfromtimestamp(exp) if exp else datetime.utcnow() + timedelta(hours=24)

        # Record revocation for token hash
        existing = session.exec(select(TokenRevocation).where(TokenRevocation.token_identifier == token_hash)).first()
        if not existing:
            revocation = TokenRevocation(
                id=str(uuid.uuid4()),
                token_identifier=token_hash,
                user_id=user_id,
                revoked_at=datetime.utcnow(),
                expires_at=expires_at,
                reason=reason
            )
            session.add(revocation)

        # Also revoke by jti if available
        jti = payload.get("jti")
        if jti:
            existing_jti = session.exec(select(TokenRevocation).where(TokenRevocation.token_identifier == jti)).first()
            if not existing_jti:
                jti_revocation = TokenRevocation(
                    id=str(uuid.uuid4()),
                    token_identifier=jti,
                    user_id=user_id,
                    revoked_at=datetime.utcnow(),
                    expires_at=expires_at,
                    reason=reason
                )
                session.add(jti_revocation)

        session.commit()
    except Exception as e:
        print(f"[Revoke Token Error]: {e}")

def revoke_all_user_tokens(user_id: str, session: Session, reason: str = "security_reset"):
    """Revokes all active refresh tokens for a user upon password change or privilege update."""
    active_tokens = session.exec(
        select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at == None)
    ).all()
    for rt in active_tokens:
        rt.revoked_at = datetime.utcnow()
        session.add(rt)
    session.commit()
