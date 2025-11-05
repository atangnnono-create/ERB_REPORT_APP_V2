from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, UTC
from backend.app.core.database import get_db
from backend.app.models import models
from backend.app.crud import crud
from backend.app.core.config import settings  # ✅ Use centralized settings
from backend.app.utils.utilities import get_secret_key, get_algorithm, decode_access_token  # ✅ Use secure functions

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")  # ✅ Use full path


# -------- Helpers --------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Create a secure password hash"""
    return pwd_context.hash(password)


# -------- Current User with Enhanced Security --------
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> models.User:
    """
    Get current user from JWT token with enhanced security checks
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # ✅ Use the secure decode function from utilities
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    # ✅ Check token expiration manually (in case decode_access_token doesn't)
    exp = payload.get("exp")
    if exp and datetime.now(UTC).timestamp() > exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )

    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception

    # ✅ Additional security checks
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # ✅ Optional: Check if user is verified (if you have email verification)
    if hasattr(user, 'is_verified') and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not verified"
        )

    return user


# -------- Optional: Role-based access --------
async def get_current_admin_user(
        current_user: models.User = Depends(get_current_user)
) -> models.User:
    """Ensure current user is an admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# -------- Token Creation (if not elsewhere) --------
def create_access_token(data: dict, expires_delta: int = None) -> str:
    """Create JWT access token"""
    from datetime import timedelta

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta(minutes=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # ✅ Use secure functions for secret key and algorithm
    encoded_jwt = jwt.encode(
        to_encode,
        get_secret_key(),
        algorithm=get_algorithm()
    )
    return encoded_jwt


# -------- Optional: Get current user without raising exceptions --------
async def get_optional_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> models.User | None:
    """
    Get current user if available, return None if not authenticated
    Useful for endpoints that work for both authenticated and unauthenticated users
    """
    if not token:
        return None

    try:
        payload = decode_access_token(token)
        if payload is None:
            return None

        username: str = payload.get("sub")
        if username is None:
            return None

        # Check token expiration
        exp = payload.get("exp")
        if exp and datetime.now(UTC).timestamp() > exp:
            return None

        user = crud.get_user_by_username(db, username=username)
        if user is None or not user.is_active:
            return None

        return user
    except Exception:
        return None