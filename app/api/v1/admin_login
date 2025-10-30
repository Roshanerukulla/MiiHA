from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.firestore_client import db
import bcrypt

router = APIRouter()

class AdminLoginRequest(BaseModel):
    email: str
    password: str

@router.post("/admin/login")
async def login_admin(admin: AdminLoginRequest):
    admin_ref = db.collection("admins").document(admin.email)
    admin_doc = admin_ref.get()

    if not admin_doc.exists:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    admin_data = admin_doc.to_dict()
    stored_hash = admin_data.get("password")

    if not bcrypt.checkpw(admin.password.encode('utf-8'), stored_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Admin login successful"}
