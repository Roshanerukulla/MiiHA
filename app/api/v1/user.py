from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from app.models.user import UserOut, UserUpdate
from app.utils.hash_utils import hash_password, verify_password
from app.db.mongodb import db
from pydantic import BaseModel

router = APIRouter()

# Get profile
@router.get("/me", response_model=UserOut)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    return current_user

# Update profile
@router.put("/me", response_model=UserOut)
async def update_my_profile(update: UserUpdate, current_user: dict = Depends(get_current_user)):
    email = current_user["email"]
    update_data = update.dict(exclude_unset=True)

    if "password" in update_data:
        del update_data["password"]

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid update fields provided")

    await db.users.update_one({"email": email}, {"$set": update_data})
    updated_user = await db.users.find_one({"email": email})
    return updated_user

# 👇 Password Update Route
class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

@router.put("/me/update_password")
async def update_password(data: PasswordUpdate, current_user: dict = Depends(get_current_user)):
    email = current_user["email"]
    user_in_db = await db.users.find_one({"email": email})

    if not verify_password(data.current_password, user_in_db["hashed_password"]):
        raise HTTPException(status_code=403, detail="Current password is incorrect")

    hashed_new_password = hash_password(data.new_password)

    await db.users.update_one({"email": email}, {"$set": {"hashed_password": hashed_new_password}})
    return {"message": "Password updated successfully"}
