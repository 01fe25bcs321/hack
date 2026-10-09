import csv
import json
from .base import ExtractionResult, IngestionError

def extract_csv(path: str) -> ExtractionResult:
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            columns = reader.fieldnames or []
        text = json.dumps({"columns": columns, "rows": rows}, ensure_ascii=False, indent=2)
        return ExtractionResult(text, {"columns": columns, "row_count": len(rows)})
    except Exception as exc:
        raise IngestionError(f"CSV extraction failed: {exc}") from exc
