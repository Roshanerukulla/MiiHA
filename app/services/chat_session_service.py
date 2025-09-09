# app/services/chat_session_services.py

from uuid import uuid4
from datetime import datetime
from app.db.firestore_client import db
from google.cloud import firestore

MAX_MESSAGES = 100

def create_chat_session(user_id: str, session_name: str = "New Chat"):
    session_id = f"{user_id}_{uuid4().hex[:10]}"
    session_data = {
        "session_id": session_id,
        "user_id": user_id,
        "session_name": session_name,
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }
    db.collection("chat_sessions").document(session_id).set(session_data)
    return {
        "session_id": session_id,
        "created_at": datetime.utcnow().isoformat(),  # return a value immediately
    }


def add_message_to_session(session_id: str, prompt: str, response: str, sources: list = None):
    messages_ref = db.collection("chat_sessions").document(session_id).collection("messages")

    existing_messages = list(messages_ref.stream())
    if len(existing_messages) >= MAX_MESSAGES:
        oldest = sorted(existing_messages, key=lambda x: x.create_time)[0]
        oldest.reference.delete()

    messages_ref.add({
        "timestamp": datetime.utcnow(),
        "prompt": prompt,
        "response": response,
        "sources": sources or []
    })

    db.collection("chat_sessions").document(session_id).update({
        "updated_at": firestore.SERVER_TIMESTAMP
    })



def get_sessions_for_user(user_id: str):
    sessions = (
        db.collection("chat_sessions")
        .where("user_id", "==", user_id)
        .order_by("updated_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    return [doc.to_dict() for doc in sessions]


def get_chat_history(session_id: str, user_id: str):
    session_ref = db.collection("chat_sessions").document(session_id)
    session_doc = session_ref.get()

    if not session_doc.exists:
        raise ValueError("Session not found")

    session = session_doc.to_dict()
    if session["user_id"] != user_id:
        raise PermissionError("Unauthorized access")

    messages_ref = session_ref.collection("messages").order_by("timestamp")
    messages = [doc.to_dict() for doc in messages_ref.stream()]

    return {
        "session_id": session_id,
        "session_name": session.get("session_name"),
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at"),
        "messages": messages
    }


def rename_session(session_id: str, user_id: str, new_name: str):
    session_ref = db.collection("chat_sessions").document(session_id)
    session_doc = session_ref.get()

    if not session_doc.exists:
        raise ValueError("Session not found")

    session = session_doc.to_dict()
    if session["user_id"] != user_id:
        raise PermissionError("Unauthorized rename")

    session_ref.update({
        "session_name": new_name,
        "updated_at": firestore.SERVER_TIMESTAMP
    })


def delete_session(session_id: str, user_id: str):
    session_ref = db.collection("chat_sessions").document(session_id)
    session_doc = session_ref.get()

    if not session_doc.exists or session_doc.to_dict().get("user_id") != user_id:
        raise PermissionError("Not allowed to delete this session")

    messages_ref = session_ref.collection("messages")
    for doc in messages_ref.stream():
        doc.reference.delete()

    session_ref.delete()
