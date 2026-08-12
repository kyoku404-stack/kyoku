from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document():
    """Ingestion API - Upload Document"""
    return {"message": "Document upload endpoint placeholder"}

@router.get("/")
async def list_documents():
    """Ingestion API - List Documents"""
    return {"documents": []}
