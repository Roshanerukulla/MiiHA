from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.firestore_client import db
import bcrypt
import google.cloud.firestore as firestore

router = APIRouter()

class AdminRegisterRequest(BaseModel):
    email: str
    password: str
    secretcode: str

@router.post("/admin/register")
async def register_admin(admin: AdminRegisterRequest):
    if admin.secretcode != "supersecret123":
        raise HTTPException(status_code=403, detail="Unauthorized entry")
    
    admin_ref = db.collection("admins").document(admin.email)
    admin_data = admin_ref.get()
    if admin_data.exists:
        raise HTTPException(status_code=400, detail="Admin already exists")

    hashed_pw = bcrypt.hashpw(admin.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    admin_ref.set({
        "email": admin.email,
        "password": hashed_pw,
        "created_at": firestore.SERVER_TIMESTAMP
    })

    return {"message": "Admin registered successfully"}
