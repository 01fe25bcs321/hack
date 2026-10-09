from .base import ExtractionResult, IngestionError

def extract_txt(path: str) -> ExtractionResult:
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return ExtractionResult(text, {})
    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                return ExtractionResult(f.read(), {"encoding": "utf-8-sig"})
        except Exception as exc:
            raise IngestionError(f"TXT decoding failed: {exc}") from exc
    except Exception as exc:
        raise IngestionError(f"TXT extraction failed: {exc}") from exc
