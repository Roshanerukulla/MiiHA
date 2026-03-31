from fastapi import APIRouter, HTTPException

from app.models.user import UserCreate
from app.services.onboarding_service import create_user
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/onboarding")
async def onboard_user(user: UserCreate):
    try:
        user_id = await create_user(user)
        return {"message": "User registered successfully", "user_id": user_id}
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))
    except Exception as e:
        logger.error(f"Registration failed for {user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")
