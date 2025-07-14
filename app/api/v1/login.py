from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models.user import UserLogin
from app.services.auth_service import authenticate_user
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Header
from app.core.jwt import decode_refresh_token, create_access_token,create_refresh_token
from app.models.token import Token
from datetime import timedelta
from typing import Optional

ACCESS_TOKEN_EXPIRE_MINUTES= 60
router = APIRouter()

@router.post("/login")
async def login(user: UserLogin):
    token = authenticate_user(user.email, user.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token["expires_in"] = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
    return token


@router.post("/refresh", response_model=Token)
async def refresh_token(authorization: Optional[str] = Header(None)):
    print("Receieved header", authorization)
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid header format")

    refresh_token = authorization.split(" ")[1]
    payload = decode_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_data = {"sub": payload["sub"]}
    new_access_token = create_access_token(user_data)
    new_refresh_token = create_refresh_token(user_data)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/logout")
async def logout__user(authorization: Optional[str] = Header(None)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail= "Invalid header format")
    
    return {"detail": "succesfully logged out"}