from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.core.jwt import decode_access_token
from app.db.firestore_client import db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Firestore version (fixed)
    users_ref = db.collection("users").where("email", "==", payload["sub"])
    results = users_ref.stream()
    user_doc = next(results, None)

    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    return user_doc.to_dict()
