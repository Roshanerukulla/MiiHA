from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.services.query_service import query_rag
from app.services.chat_session_service import (
    create_chat_session,
    add_message_to_session,
    get_sessions_for_user,
    get_chat_history,
    rename_session,
    delete_session
)

router = APIRouter()

# 🚀 Start a new chat session
class SessionCreateRequest(BaseModel):
    session_name: str = "New Chat"

@router.post("/chat/session")
async def start_chat_session(
    request: SessionCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user")

    session_id = create_chat_session(user_id, request.session_name)
    return {"message": "Session created", "session_id": session_id}


# 🧠 Handle prompt and get LLM response
class MessageRequest(BaseModel):
    session_id: str
    prompt: str

@router.post("/chat/send")
async def send_message(
    request: MessageRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user")

    # 🧠 Load prior messages to build context
    try:
        history = get_chat_history(request.session_id, user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed to access this session")

    # 💬 Convert last 10 messages to chat-style format (preserve flow)
    raw_messages = history["messages"][-10:]  # Last 10 exchanges
    chat_history = []
    for msg in raw_messages:
        chat_history.append({"role": "user", "content": msg["prompt"]})
        chat_history.append({"role": "assistant", "content": msg["response"]})

    # 🔍 Run RAG with prompt + history
    rag_result = query_rag(request.prompt, chat_history=chat_history)

    # 💾 Save new prompt-response pair
    try:
        add_message_to_session(request.session_id, request.prompt, rag_result["answer"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")

    return {
        "session_id": request.session_id,
        "answer": rag_result["answer"],
        "sources": rag_result["sources"]
    }



# 📋 List all sessions for a user
@router.get("/chat/sessions")
async def list_user_sessions(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user")

    sessions = get_sessions_for_user(user_id)
    return {"sessions": sessions}


# 💬 Get full chat history for a session
@router.get("/chat/session/{session_id}")
async def fetch_chat_history(session_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user")

    try:
        history = get_chat_history(session_id, user_id)
        return history
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed to access this session")


# ✏️ Rename a session
class RenameRequest(BaseModel):
    new_name: str

@router.put("/chat/session/{session_id}")
async def rename_chat_session(
    session_id: str,
    request: RenameRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("user_id")
    try:
        rename_session(session_id, user_id, request.new_name)
        return {"message": "Session renamed successfully"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed to rename this session")


# 🗑️ Delete a session
@router.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    try:
        delete_session(session_id, user_id)
        return {"message": "Session deleted successfully"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed to delete this session")
