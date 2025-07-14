from app.utils.hash_utils import verify_password
from app.db.firestore_client import db
from app.core.jwt import create_access_token, create_refresh_token

def authenticate_user(email: str, password: str):
    email = email.lower()
    users_collection = db.collection("users")
    query = users_collection.where("email", "==", email)

    results = list(query.stream())
    user_doc = results[0] if results else None

    if not user_doc or not verify_password(password, user_doc.to_dict().get("hashed_password", "")):
        return None

    data = {"sub": user_doc.to_dict()["email"]}
    return {
        "access_token": create_access_token(data),
        "refresh_token": create_refresh_token(data),
        "token_type": "bearer"
    }
