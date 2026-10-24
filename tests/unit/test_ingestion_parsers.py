"""Unit tests for MultiFormatDocumentParser and DefaultOCRProcessor (Phase 2.1).

Tests multi-format file extraction, OCR fallbacks, and content normalization.
Specification: devdocs/p2/p2.txt Chapter 17 & docs/Architecture/ai-ingestion-pipeline.md
Owner: Member 2 (Backend Lead)
"""

import zipfile
from uuid import uuid4

import pytest

from backend.app.services.ai.ingestion import (
    DocumentParserType,
    OCRProcessingEngine,
)
from backend.app.services.ingestion.ocr import DefaultOCRProcessor
from backend.app.services.ingestion.parser import MultiFormatDocumentParser


@pytest.mark.asyncio
async def test_markdown_extraction(tmp_path):
    """Verifies that Markdown text and headers are accurately parsed into sections."""
    md_content = """# Executive Summary
This is the enterprise knowledge base overview.

## Architecture
KEEP employs a multi-tenant microservices architecture.

### Storage Subsystem
PostgreSQL 16 and MinIO object storage handle assets.
"""
    file_path = tmp_path / "test_doc.md"
    file_path.write_text(md_content, encoding="utf-8")

    parser = MultiFormatDocumentParser()
    doc_id = uuid4()
    version_id = uuid4()

    result = await parser.extract(str(file_path), doc_id, version_id)

    assert result.document_id == doc_id
    assert result.file_type == DocumentParserType.MARKDOWN
    assert not result.requires_ocr
    assert len(result.sections) >= 3
    assert result.sections[0].title == "Executive Summary"
    assert "enterprise knowledge base overview" in result.sections[0].text
    assert result.sections[1].title == "Architecture"


@pytest.mark.asyncio
async def test_plain_text_extraction(tmp_path):
    """Verifies that plain text files are parsed into single-section content."""
    text_content = "Simple raw text note without structured formatting."
    file_path = tmp_path / "simple.txt"
    file_path.write_text(text_content, encoding="utf-8")

    parser = MultiFormatDocumentParser()
    result = await parser.extract(str(file_path), uuid4(), uuid4())

    assert result.file_type == DocumentParserType.TXT
    assert not result.requires_ocr
    assert len(result.sections) == 1
    assert "Simple raw text" in result.raw_text


@pytest.mark.asyncio
async def test_csv_extraction(tmp_path):
    """Verifies tabular parsing and row formatting for CSV files."""
    csv_content = "EmployeeID,FullName,Department\n101,Alice Smith,Engineering\n102,Bob Jones,Finance\n"
    file_path = tmp_path / "data.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    parser = MultiFormatDocumentParser()
    result = await parser.extract(str(file_path), uuid4(), uuid4())

    assert result.file_type == DocumentParserType.CSV
    assert result.has_tables
    assert "101 | Alice Smith | Engineering" in result.raw_text
    assert "102 | Bob Jones | Finance" in result.raw_text


@pytest.mark.asyncio
async def test_image_ocr_flagging(tmp_path):
    """Verifies that image files are flagged for OCR processing."""
    file_path = tmp_path / "scan.png"
    file_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)

    parser = MultiFormatDocumentParser()
    result = await parser.extract(str(file_path), uuid4(), uuid4())

    assert result.file_type == DocumentParserType.IMAGE_OCR
    assert result.requires_ocr
    assert result.raw_text == ""


@pytest.mark.asyncio
async def test_synthetic_docx_extraction(tmp_path):
    """Verifies OpenXML DOCX archive extraction."""
    file_path = tmp_path / "document.docx"
    doc_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:body>
            <w:p>
                <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
                <w:r><w:t>Project Specification</w:t></w:r>
            </w:p>
            <w:p>
                <w:r><w:t>This is an enterprise document processed via OpenXML parser.</w:t></w:r>
            </w:p>
        </w:body>
    </w:document>"""

    with zipfile.ZipFile(file_path, "w") as z:
        z.writestr("word/document.xml", doc_xml)

    parser = MultiFormatDocumentParser()
    result = await parser.extract(str(file_path), uuid4(), uuid4())

    assert result.file_type == DocumentParserType.DOCX
    assert not result.requires_ocr
    assert "Project Specification" in result.raw_text
    assert "processed via OpenXML parser" in result.raw_text


@pytest.mark.asyncio
async def test_ocr_processor_mock_and_pdf(tmp_path):
    """Verifies DefaultOCRProcessor handles image bytes and scanned PDF extraction."""
    ocr = DefaultOCRProcessor(engine=OCRProcessingEngine.MOCK)

    sample_bytes = b"fake-scanned-image-pixels"
    text = await ocr.extract_text_from_image(sample_bytes)
    assert "[OCR Extracted Content]" in text
    assert "MOCK" in text

    dummy_pdf = tmp_path / "empty_scan.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.4\n%EOF")
    pages = await ocr.process_scanned_pdf(str(dummy_pdf))
    assert len(pages) >= 1
    assert "optical text recovered" in pages[0]
