"""
Utility for converting PDF files to clean markdown text using docling.

Docling preserves document structure (headings, tables, lists) which improves
chunking quality and entity extraction in downstream RAG pipelines.
"""

from __future__ import annotations


def pdf_to_markdown(pdf_path: str) -> str:
    """Convert a PDF file to a markdown string using docling.

    Uses docling's DocumentConverter which handles:
    - Text-layer PDFs (fast, no OCR needed)
    - Scanned PDFs (falls back to OCR)
    - Tables, headings, lists (exported as markdown)

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        Markdown-formatted string of the document content.

    Raises:
        ImportError: If docling is not installed.
        FileNotFoundError: If the PDF file does not exist.
        RuntimeError: If docling fails to convert the document.
    """
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as e:
        raise ImportError(
            "docling is required for PDF ingestion. "
            "Install it with: pip install docling"
        ) from e

    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    return result.document.export_to_markdown()
