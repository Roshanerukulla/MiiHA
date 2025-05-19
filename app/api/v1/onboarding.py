from fastapi import APIRouter, HTTPException
from app.models.user import UserCreate
from app.services.onboarding_service import create_user

router = APIRouter()

@router.post("/onboarding")
async def onboard_user(user: UserCreate):
    try:
        user_id = await create_user(user)
        return {"message": "User registered successfully", "user_id": user_id}
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))  # Conflict
    except Exception as e:
        raise HTTPException(status_code=500, detail="Something went wrong")
