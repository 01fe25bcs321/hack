import json
from .base import ExtractionResult, IngestionError

def extract_json(path: str) -> ExtractionResult:
    try:
        with open(path, "r", encoding="utf-8") as f:
            value = json.load(f)
        return ExtractionResult(json.dumps(value, ensure_ascii=False, indent=2), {"json_type": type(value).__name__})
    except json.JSONDecodeError as exc:
        raise IngestionError(f"Invalid JSON: {exc.msg} at line {exc.lineno}") from exc
    except Exception as exc:
        raise IngestionError(f"JSON extraction failed: {exc}") from exc
