from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
oauth2_optional = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exc
    except InvalidTokenError as exc:
        raise credentials_exc from exc

    user = db.get(User, UUID(user_id))
    if not user or not user.is_active:
        raise credentials_exc
    return user


def apply_updates(instance, data: dict) -> None:
    for key, value in data.items():
        if value is not None:
            setattr(instance, key, value)
    if hasattr(instance, "updated_at"):
        instance.updated_at = datetime.now(timezone.utc)
