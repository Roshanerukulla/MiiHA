from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from app.core.dependencies import get_current_user
from app.services.query_service import query_rag

router = APIRouter()


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be blank")
        return v.strip()


@router.post("/query/full")
async def full_query_service(request: QueryRequest, user: dict = Depends(get_current_user)):
    return await query_rag(request.query, top_k=request.top_k)
