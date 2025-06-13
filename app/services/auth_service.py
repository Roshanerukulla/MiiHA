from app.utils.hash_utils import verify_password
from app.db.mongodb import db
from app.core.jwt import create_access_token,create_refresh_token

async def authenticate_user(email: str, password: str):
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(password, user["hashed_password"]):
        return None

   
    data = {"sub": user["email"]}
    return {
        "access_token": create_access_token(data),
        "refresh_token": create_refresh_token(data),
        "token_type": "bearer"
    }