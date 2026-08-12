from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/query")
async def chat_query():
    """RAG Query Stream - Process Query"""
    return {"message": "Chat RAG query endpoint placeholder"}
