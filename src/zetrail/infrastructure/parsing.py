import pymupdf
from pathlib import Path
from domain.documents.blocks import TextBlock


def parse_pdf(path: Path, max_pages: int, max_text_chars: int) -> list[TextBlock]:
    blocks = []
    size = 0
    with pymupdf.open(path) as document:
        if not document.is_pdf or document.needs_pass:
            raise ValueError("Invalid or encrypted PDF")
        if len(document) > max_pages:
            raise ValueError("Page limit exceeded")
        for number, page in enumerate(document, start = 1):
            text = page.get_text("text", sort = True).replace("\x00", "").strip()
            size += len(text)
            if size > max_text_chars:
                raise ValueError("Text limit exceeded")
            if text:
                blocks.append(TextBlock(page = number, text = text))
    return blocks
