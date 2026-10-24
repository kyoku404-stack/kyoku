"""KEEP Enterprise Platform — Ingestion Services Package (Phase 2.1).

Exports document parser, OCR processor, and ingestion service.
Specification: devdocs/p2/p2.1.txt & docs/Architecture/ai-ingestion-pipeline.md
Owner: Member 2 (Backend Lead)
"""

from backend.app.services.ingestion.ocr import DefaultOCRProcessor
from backend.app.services.ingestion.parser import MultiFormatDocumentParser
from backend.app.services.ingestion.service import IngestionService

__all__ = [
    "DefaultOCRProcessor",
    "IngestionService",
    "MultiFormatDocumentParser",
]
