from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from app.models.user import UserOut, UserUpdate
from app.utils.hash_utils import hash_password, verify_password
from app.db.firestore_client import db
from pydantic import BaseModel, EmailStr
from app.services.firestore_user_service import invalidate_user_cache


router = APIRouter()

# ✅ Get current profile
@router.get("/me", response_model=UserOut)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    return current_user

# ✅ Update profile
@router.put("/me", response_model=UserOut)
async def update_my_profile(update: UserUpdate, current_user: dict = Depends(get_current_user)):
    email = current_user["email"]
    update_data = update.dict(exclude_unset=True)

    if "password" in update_data:
        del update_data["password"]

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid update fields provided")

    users = db.collection("users").where("email", "==", email).stream()
    user_doc = next(users, None)

    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    user_ref = db.collection("users").document(user_doc.id)
    user_ref.update(update_data)

    # ✅ Invalidate cached profile
    await invalidate_user_cache(current_user["user_id"])

    updated_user = user_ref.get().to_dict()
    return updated_user

# ✅ Change password (requires login + current password)
class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

@router.put("/me/update_password")
async def update_password(data: PasswordUpdate, current_user: dict = Depends(get_current_user)):
    email = current_user["email"]

    users = db.collection("users").where("email", "==", email).stream()
    user_doc = next(users, None)

    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user_doc.to_dict()
    if not verify_password(data.current_password, user_data["hashed_password"]):
        raise HTTPException(status_code=403, detail="Current password is incorrect")

    new_hashed_password = hash_password(data.new_password)

    db.collection("users").document(user_doc.id).update({
        "hashed_password": new_hashed_password
    })

    return {"message": "Password updated successfully"}

# ✅ Reset password (just email + new password)
class PasswordResetRequest(BaseModel):
    email: EmailStr
    new_password: str

@router.post("/reset_password")
async def reset_password(data: PasswordResetRequest):
    users = db.collection("users").where("email", "==", data.email).stream()
    user_doc = next(users, None)

    if not user_doc:
        raise HTTPException(status_code=404, detail="Email not found")

    new_hashed_password = hash_password(data.new_password)
    db.collection("users").document(user_doc.id).update({
        "hashed_password": new_hashed_password
    })

    return {"message": "Password reset successfully"}
