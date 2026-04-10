from typing import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_jwt
from app.db.session import get_db
from app.db.models.user import User

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency for protected endpoints.
    Full implementation in D-003 (Auth).
    This skeleton raises 401 for all requests — replaced in D-003.
    """
    if not credentials:
        raise UnauthorizedError()
    payload = decode_jwt(credentials.credentials)
    if not payload:
        raise UnauthorizedError("Invalid token")
    # Full DB lookup implemented in D-003
    raise UnauthorizedError("Auth service not yet initialized")


async def require_pro(user: User = Depends(get_current_user)) -> User:
    """Dependency for Pro-gated endpoints."""
    if not user.is_pro:
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError()
    return user
