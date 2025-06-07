from app.models.user import UserCreate
from app.utils.hash_utils import hash_password
from app.db.mongodb import db

async def create_user(user_data: UserCreate) -> str:
    user_dict = user_data.dict()

    # ✅ Check if email already exists
    existing_user = await db.users.find_one({"email": user_dict["email"]})
    if existing_user:
        raise ValueError("Email already registered")

    # ✅ Hash password before storing
    user_dict["hashed_password"] = hash_password(user_dict.pop("password"))

    result = await db.users.insert_one(user_dict)
    
    return str(result.inserted_id)
