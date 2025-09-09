from fastapi import APIRouter, HTTPException, Request
from app.db.firestore_client import db
import os

router = APIRouter()

# ✅ Load cleanup secret from environment
CLEANUP_SECRET = os.getenv("CLEANUP_SECRET")

@router.get("/cleanup", tags=["Maintenance"])
def cleanup_sessions(request: Request):
    token = request.headers.get("x-cleanup-token")
    if token != CLEANUP_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    sessions = db.collection("chat_sessions").stream()
    deleted = 0

    for s in sessions:
        messages = (
            db.collection("chat_sessions")
            .document(s.id)
            .collection("messages")
            .limit(1)
            .stream()
        )
        if len(list(messages)) == 0:
            db.collection("chat_sessions").document(s.id).delete()
            deleted += 1

    return {"status": "success", "deleted_sessions": deleted}
