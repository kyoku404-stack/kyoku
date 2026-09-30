"""KEEP Enterprise Platform — Search Schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SearchFilter(BaseModel):
    """Optional search filter attributes."""

    document_types: list[str] | None = Field(default=None, description="Filter by file extension")
    document_ids: list[UUID] | None = Field(default=None, description="Filter by specific document IDs")


class HybridSearchRequest(BaseModel):
    """Payload for hybrid vector + keyword search."""

    query: str = Field(..., min_length=1, max_length=1000, description="User search query")
    top_k: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    filters: SearchFilter | None = Field(default=None, description="Metadata filters")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "enterprise remote work guidelines and stipend",
                "top_k": 10,
                "filters": {
                    "document_types": ["pdf", "docx"],
                },
            }
        }
    )


class SearchResultItem(BaseModel):
    """Individual search result item."""

    chunk_id: UUID = Field(..., description="Unique chunk identifier")
    document_id: UUID = Field(..., description="Parent document identifier")
    filename: str = Field(..., description="Document source filename")
    page_number: int | None = Field(default=None, description="Document page number")
    content: str = Field(..., description="Matching text excerpt")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Normalized relevance score")


class SearchResponse(BaseModel):
    """Search results response payload."""

    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Count of returned items")
    results: list[SearchResultItem] = Field(default_factory=list, description="Ranked search results")
