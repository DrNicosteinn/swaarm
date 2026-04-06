"""Authentication dependencies for FastAPI using Supabase JWT."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from pydantic import BaseModel

from app.core.supabase import get_supabase_client

security = HTTPBearer()


class AuthUser(BaseModel):
    """Authenticated user extracted from Supabase JWT."""

    id: str
    email: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthUser:
    """Validate Supabase JWT and return the authenticated user.

    Raises HTTPException 401 if the token is invalid or expired.
    """
    token = credentials.credentials

    try:
        supabase = get_supabase_client()
        response = supabase.auth.get_user(token)

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungültiger oder abgelaufener Token",
            )

        return AuthUser(
            id=response.user.id,
            email=response.user.email or "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e!s}")  # Log real error server-side only
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentifizierung fehlgeschlagen",  # Generic message to client
        ) from e
