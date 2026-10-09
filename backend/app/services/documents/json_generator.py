import json
from pathlib import Path

def write_json(document: dict, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
