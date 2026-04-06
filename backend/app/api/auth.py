"""Auth-related API endpoints."""

from fastapi import APIRouter, Depends

from app.core.auth import AuthUser, get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(user: AuthUser = Depends(get_current_user)) -> dict:
    """Return the currently authenticated user's info."""
    return {
        "id": user.id,
        "email": user.email,
    }
