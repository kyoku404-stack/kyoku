"""KEEP Enterprise Platform — Multi-Format Document Parser (Phase 2.1).

Implements BaseDocumentExtractor for PDF, DOCX, TXT, Markdown, PPTX, XLSX, CSV,
and image formats, extracting text, sections, and structural layout metadata.
Specification: devdocs/p2/p2.1.txt Chapters 4, 5 & docs/Architecture/ai-ingestion-pipeline.md
Owner: Member 2 (Backend Lead)
"""

import csv
import io
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import ClassVar
from uuid import UUID

from backend.app.services.ai.ingestion import (
    BaseDocumentExtractor,
    DocumentParserType,
    ExtractedDocumentContent,
    ExtractedSection,
)


class MultiFormatDocumentParser(BaseDocumentExtractor):
    """Production document parser supporting all standard enterprise formats."""

    SUPPORTED_EXTENSIONS: ClassVar[dict[str, DocumentParserType]] = {
        ".pdf": DocumentParserType.PDF,
        ".docx": DocumentParserType.DOCX,
        ".doc": DocumentParserType.DOCX,
        ".txt": DocumentParserType.TXT,
        ".md": DocumentParserType.MARKDOWN,
        ".markdown": DocumentParserType.MARKDOWN,
        ".pptx": DocumentParserType.PPTX,
        ".xlsx": DocumentParserType.XLSX,
        ".csv": DocumentParserType.CSV,
        ".png": DocumentParserType.IMAGE_OCR,
        ".jpg": DocumentParserType.IMAGE_OCR,
        ".jpeg": DocumentParserType.IMAGE_OCR,
        ".webp": DocumentParserType.IMAGE_OCR,
        ".tiff": DocumentParserType.IMAGE_OCR,
    }

    async def extract(
        self,
        file_path: str,
        document_id: UUID,
        version_id: UUID,
        mime_type: str = "text/plain",
    ) -> ExtractedDocumentContent:
        """Parses document from filesystem and extracts structured text and sections."""
        path = Path(file_path)
        ext = path.suffix.lower()
        parser_type = self.SUPPORTED_EXTENSIONS.get(ext, DocumentParserType.TXT)

        if not path.exists():
            raise FileNotFoundError(f"Document file not found at path: {file_path}")

        file_bytes = path.read_bytes()

        if parser_type == DocumentParserType.PDF:
            return self._extract_pdf(file_bytes, document_id, version_id, path.name)
        elif parser_type == DocumentParserType.DOCX:
            return self._extract_docx(file_bytes, document_id, version_id, path.name)
        elif parser_type == DocumentParserType.PPTX:
            return self._extract_pptx(file_bytes, document_id, version_id, path.name)
        elif parser_type == DocumentParserType.XLSX:
            return self._extract_xlsx(file_bytes, document_id, version_id, path.name)
        elif parser_type == DocumentParserType.CSV:
            return self._extract_csv(file_bytes, document_id, version_id, path.name)
        elif parser_type == DocumentParserType.MARKDOWN:
            return self._extract_markdown(file_bytes, document_id, version_id, path.name)
        elif parser_type == DocumentParserType.IMAGE_OCR:
            return self._extract_image(file_bytes, document_id, version_id, path.name, ext)
        else:
            return self._extract_plain_text(file_bytes, document_id, version_id, path.name)

    def _extract_pdf(
        self,
        file_bytes: bytes,
        document_id: UUID,
        version_id: UUID,
        filename: str,
    ) -> ExtractedDocumentContent:
        """Extracts text page-by-page from PDF files using pypdf."""
        raw_text_parts: list[str] = []
        sections: list[ExtractedSection] = []
        total_pages = 1
        requires_ocr = False

        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(file_bytes))
            total_pages = len(reader.pages) or 1
            has_text_found = False

            for page_idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                cleaned_page = page_text.strip()
                if cleaned_page:
                    has_text_found = True
                    raw_text_parts.append(cleaned_page)
                    first_line = cleaned_page.split("\n")[0][:120].strip()
                    sections.append(
                        ExtractedSection(
                            title=first_line or f"Page {page_idx}",
                            level=1,
                            text=cleaned_page,
                            page_number=page_idx,
                            order_index=page_idx - 1,
                            token_count_estimate=len(cleaned_page.split()),
                        )
                    )

            if not has_text_found:
                requires_ocr = True
        except (ImportError, OSError, ValueError):
            requires_ocr = True

        full_text = "\n\n".join(raw_text_parts)
        return ExtractedDocumentContent(
            document_id=document_id,
            document_version_id=version_id,
            raw_text=full_text,
            sections=sections,
            total_pages=total_pages,
            file_type=DocumentParserType.PDF,
            has_tables=False,
            requires_ocr=requires_ocr,
            metadata={"filename": filename, "source": "pypdf_extractor"},
        )

    def _extract_docx(
        self,
        file_bytes: bytes,
        document_id: UUID,
        version_id: UUID,
        filename: str,
    ) -> ExtractedDocumentContent:
        """Extracts text, headings, and paragraph hierarchy from DOCX XML payload."""
        sections: list[ExtractedSection] = []
        paragraphs: list[str] = []
        current_section_title = "Document Body"
        current_section_lines: list[str] = []
        current_section_level = 1
        section_idx = 0

        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as docx_zip:
                xml_content = docx_zip.read("word/document.xml")
                root = ET.fromstring(xml_content)

                namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

                for p_elem in root.iterfind(".//w:p", namespaces):
                    is_heading = False
                    heading_level = 1
                    style_elem = p_elem.find(".//w:pPr/w:pStyle", namespaces)
                    if style_elem is not None:
                        val = style_elem.attrib.get(f"{{{namespaces['w']}}}val", "")
                        if "Heading" in val or "heading" in val:
                            is_heading = True
                            digits = re.findall(r"\d+", val)
                            heading_level = int(digits[0]) if digits else 1

                    texts = [
                        node.text
                        for node in p_elem.iterfind(".//w:t", namespaces)
                        if node.text
                    ]
                    p_text = "".join(texts).strip()
                    if not p_text:
                        continue

                    if is_heading:
                        if current_section_lines:
                            sec_text = "\n".join(current_section_lines)
                            sections.append(
                                ExtractedSection(
                                    title=current_section_title,
                                    level=current_section_level,
                                    text=sec_text,
                                    page_number=1,
                                    order_index=section_idx,
                                    token_count_estimate=len(sec_text.split()),
                                )
                            )
                            section_idx += 1
                            current_section_lines = []
                        current_section_title = p_text
                        current_section_level = heading_level

                    current_section_lines.append(p_text)
                    paragraphs.append(p_text)

                if current_section_lines:
                    sec_text = "\n".join(current_section_lines)
                    sections.append(
                        ExtractedSection(
                            title=current_section_title,
                            level=current_section_level,
                            text=sec_text,
                            page_number=1,
                            order_index=section_idx,
                            token_count_estimate=len(sec_text.split()),
                        )
                    )
        except (zipfile.BadZipFile, ET.ParseError, KeyError, UnicodeDecodeError, OSError):
            decoded = file_bytes.decode("utf-8", errors="ignore")
            paragraphs = [p.strip() for p in decoded.split("\n") if p.strip()]

        full_text = "\n\n".join(paragraphs)
        return ExtractedDocumentContent(
            document_id=document_id,
            document_version_id=version_id,
            raw_text=full_text,
            sections=sections,
            total_pages=max(1, len(paragraphs) // 10),
            file_type=DocumentParserType.DOCX,
            has_tables=False,
            requires_ocr=False,
            metadata={"filename": filename, "source": "openxml_extractor"},
        )

    def _extract_pptx(
        self,
        file_bytes: bytes,
        document_id: UUID,
        version_id: UUID,
        filename: str,
    ) -> ExtractedDocumentContent:
        """Extracts text slide-by-slide from PPTX presentations."""
        sections: list[ExtractedSection] = []
        all_slides_text: list[str] = []
        slide_count = 0

        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as pptx_zip:
                slide_names = sorted(
                    [
                        n
                        for n in pptx_zip.namelist()
                        if n.startswith("ppt/slides/slide") and n.endswith(".xml")
                    ]
                )
                slide_count = len(slide_names) or 1
                ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

                for idx, name in enumerate(slide_names, start=1):
                    xml_content = pptx_zip.read(name)
                    root = ET.fromstring(xml_content)
                    slide_texts = [
                        node.text
                        for node in root.iterfind(".//a:t", ns)
                        if node.text and node.text.strip()
                    ]
                    combined_slide_text = "\n".join(slide_texts).strip()
                    if combined_slide_text:
                        all_slides_text.append(f"--- Slide {idx} ---\n{combined_slide_text}")
                        sections.append(
                            ExtractedSection(
                                title=f"Slide {idx}",
                                level=1,
                                text=combined_slide_text,
                                page_number=idx,
                                order_index=idx - 1,
                                token_count_estimate=len(combined_slide_text.split()),
                            )
                        )
        except (zipfile.BadZipFile, ET.ParseError, KeyError, UnicodeDecodeError, OSError):
            all_slides_text = ["Presentation content could not be parsed."]

        return ExtractedDocumentContent(
            document_id=document_id,
            document_version_id=version_id,
            raw_text="\n\n".join(all_slides_text),
            sections=sections,
            total_pages=max(1, slide_count),
            file_type=DocumentParserType.PPTX,
            has_tables=False,
            requires_ocr=False,
            metadata={"filename": filename, "source": "pptx_extractor"},
        )

    def _extract_xlsx(
        self,
        file_bytes: bytes,
        document_id: UUID,
        version_id: UUID,
        filename: str,
    ) -> ExtractedDocumentContent:
        """Extracts structured sheets and tabular cells from XLSX spreadsheets."""
        shared_strings: list[str] = []
        sheet_texts: list[str] = []
        sections: list[ExtractedSection] = []

        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as xlsx_zip:
                ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                if "xl/sharedStrings.xml" in xlsx_zip.namelist():
                    root_ss = ET.fromstring(xlsx_zip.read("xl/sharedStrings.xml"))
                    shared_strings = [
                        node.text or ""
                        for node in root_ss.iterfind(".//s:t", ns)
                    ]

                sheet_names = sorted(
                    [
                        n
                        for n in xlsx_zip.namelist()
                        if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
                    ]
                )
                for idx, sheet_file in enumerate(sheet_names, start=1):
                    sheet_root = ET.fromstring(xlsx_zip.read(sheet_file))
                    rows_text: list[str] = []
                    for row in sheet_root.iterfind(".//s:row", ns):
                        row_cells: list[str] = []
                        for cell in row.iterfind(".//s:c", ns):
                            val_elem = cell.find("s:v", ns)
                            if val_elem is not None and val_elem.text:
                                cell_val = val_elem.text
                                cell_type = cell.attrib.get("t", "")
                                if cell_type == "s" and cell_val.isdigit():
                                    idx_s = int(cell_val)
                                    if 0 <= idx_s < len(shared_strings):
                                        cell_val = shared_strings[idx_s]
                                row_cells.append(cell_val)
                        if row_cells:
                            rows_text.append(" | ".join(row_cells))

                    if rows_text:
                        combined_sheet = "\n".join(rows_text)
                        sheet_texts.append(f"--- Sheet {idx} ---\n{combined_sheet}")
                        sections.append(
                            ExtractedSection(
                                title=f"Sheet {idx}",
                                level=1,
                                text=combined_sheet,
                                page_number=idx,
                                order_index=idx - 1,
                                token_count_estimate=len(combined_sheet.split()),
                            )
                        )
        except (zipfile.BadZipFile, ET.ParseError, KeyError, UnicodeDecodeError, OSError):
            sheet_texts = ["Spreadsheet content extraction fallback."]

        return ExtractedDocumentContent(
            document_id=document_id,
            document_version_id=version_id,
            raw_text="\n\n".join(sheet_texts),
            sections=sections,
            total_pages=max(1, len(sections)),
            file_type=DocumentParserType.XLSX,
            has_tables=True,
            requires_ocr=False,
            metadata={"filename": filename, "source": "xlsx_extractor"},
        )

    def _extract_csv(
        self,
        file_bytes: bytes,
        document_id: UUID,
        version_id: UUID,
        filename: str,
    ) -> ExtractedDocumentContent:
        """Extracts tabular records from CSV files."""
        decoded = file_bytes.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(decoded))
        formatted_rows: list[str] = []

        for row in reader:
            if row:
                formatted_rows.append(" | ".join(row))

        raw_text = "\n".join(formatted_rows)
        section = ExtractedSection(
            title=f"CSV Data: {filename}",
            level=1,
            text=raw_text,
            page_number=1,
            order_index=0,
            token_count_estimate=len(raw_text.split()),
        )

        return ExtractedDocumentContent(
            document_id=document_id,
            document_version_id=version_id,
            raw_text=raw_text,
            sections=[section],
            total_pages=1,
            file_type=DocumentParserType.CSV,
            has_tables=True,
            requires_ocr=False,
            metadata={"filename": filename, "source": "csv_extractor"},
        )

    def _extract_markdown(
        self,
        file_bytes: bytes,
        document_id: UUID,
        version_id: UUID,
        filename: str,
    ) -> ExtractedDocumentContent:
        """Extracts text and hierarchical headings from Markdown documents."""
        text = file_bytes.decode("utf-8", errors="replace")
        lines = text.split("\n")
        sections: list[ExtractedSection] = []

        current_heading = "Overview"
        current_level = 1
        current_lines: list[str] = []
        order_index = 0

        for line in lines:
            if line.startswith("#"):
                match = re.match(r"^(#+)\s*(.*)", line)
                if match:
                    if current_lines:
                        sec_body = "\n".join(current_lines).strip()
                        if sec_body:
                            sections.append(
                                ExtractedSection(
                                    title=current_heading,
                                    level=current_level,
                                    text=sec_body,
                                    page_number=1,
                                    order_index=order_index,
                                    token_count_estimate=len(sec_body.split()),
                                )
                            )
                            order_index += 1
                            current_lines = []

                    current_level = min(3, len(match.group(1)))
                    current_heading = match.group(2).strip() or f"Section {order_index + 1}"
                    continue

            current_lines.append(line)

        if current_lines:
            sec_body = "\n".join(current_lines).strip()
            if sec_body:
                sections.append(
                    ExtractedSection(
                        title=current_heading,
                        level=current_level,
                        text=sec_body,
                        page_number=1,
                        order_index=order_index,
                        token_count_estimate=len(sec_body.split()),
                    )
                )

        return ExtractedDocumentContent(
            document_id=document_id,
            document_version_id=version_id,
            raw_text=text,
            sections=sections,
            total_pages=max(1, len(text) // 2500 + 1),
            file_type=DocumentParserType.MARKDOWN,
            has_tables="|" in text,
            requires_ocr=False,
            metadata={"filename": filename, "source": "markdown_extractor"},
        )

    def _extract_plain_text(
        self,
        file_bytes: bytes,
        document_id: UUID,
        version_id: UUID,
        filename: str,
    ) -> ExtractedDocumentContent:
        """Extracts raw text from generic text documents."""
        text = file_bytes.decode("utf-8", errors="replace")
        section = ExtractedSection(
            title=f"Document: {filename}",
            level=1,
            text=text,
            page_number=1,
            order_index=0,
            token_count_estimate=len(text.split()),
        )
        return ExtractedDocumentContent(
            document_id=document_id,
            document_version_id=version_id,
            raw_text=text,
            sections=[section],
            total_pages=max(1, len(text) // 2500 + 1),
            file_type=DocumentParserType.TXT,
            has_tables=False,
            requires_ocr=False,
            metadata={"filename": filename, "source": "text_extractor"},
        )

    def _extract_image(
        self,
        file_bytes: bytes,
        document_id: UUID,
        version_id: UUID,
        filename: str,
        ext: str,
    ) -> ExtractedDocumentContent:
        """Flags image assets for downstream OCR classification and processing."""
        return ExtractedDocumentContent(
            document_id=document_id,
            document_version_id=version_id,
            raw_text="",
            sections=[],
            total_pages=1,
            file_type=DocumentParserType.IMAGE_OCR,
            has_tables=False,
            requires_ocr=True,
            metadata={"filename": filename, "format": ext, "size_bytes": len(file_bytes)},
        )
