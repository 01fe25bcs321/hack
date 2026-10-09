from pathlib import Path
from .base import ExtractionResult, IngestionError
from .pdf import extract_pdf
from .docx import extract_docx
from .txt import extract_txt
from .csv import extract_csv
from .json import extract_json
from .web import extract_web

def extract_file(path: str) -> ExtractionResult:
    ext = Path(path).suffix.lower()
    funcs = {".pdf": extract_pdf, ".docx": extract_docx, ".txt": extract_txt, ".csv": extract_csv, ".json": extract_json}
    if ext not in funcs:
        raise IngestionError(f"Unsupported file type: {ext}")
    return funcs[ext](path)
