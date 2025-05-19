from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models.user import UserLogin
from app.services.auth_service import authenticate_user

router = APIRouter()

@router.post("/login")
async def login(user: UserLogin):
    token = await authenticate_user(user.email, user.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": token, "token_type": "bearer"}
