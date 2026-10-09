import fitz
from .base import ExtractionResult, IngestionError


def extract_pdf(path: str) -> ExtractionResult:
    try:
        doc = fitz.open(path)
        pages = []
        ocr_attempted = False
        ocr_succeeded = False
        ocr_unavailable = False
        for index, page in enumerate(doc):
            text = page.get_text("text").strip()
            ocr_used = False
            if not text:
                ocr_attempted = True
                try:
                    text_page = page.get_textpage_ocr()
                    text = page.get_text("text", textpage=text_page).strip()
                    ocr_used = bool(text)
                    ocr_succeeded = ocr_succeeded or bool(text)
                except Exception:
                    ocr_unavailable = True
            pages.append({"page": index + 1, "text": text, "ocr_used": ocr_used})
        full_text = "\n\n".join(item["text"] for item in pages if item["text"])
        metadata = {
            "page_count": len(doc),
            "pages": pages,
            "pdf_metadata": doc.metadata or {},
            "ocr_attempted": ocr_attempted,
            "ocr_used": ocr_succeeded,
            "ocr_status": "completed" if ocr_succeeded else ("unavailable" if ocr_unavailable else "not_needed"),
            "pages_without_text": [item["page"] for item in pages if not item["text"]],
        }
        doc.close()
        return ExtractionResult(text=full_text, metadata=metadata)
    except Exception as exc:
        raise IngestionError(f"PDF extraction failed: {exc}") from exc
