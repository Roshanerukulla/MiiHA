from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.query_service import query_rag
from app.core.dependencies import get_current_user
from app.services.query_service import query_rag
router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3


@router.post("/query/full")
async def full_query_service(request: QueryRequest, user: dict = Depends(get_current_user)):
    return query_rag(request.query, top_k=request.top_k)