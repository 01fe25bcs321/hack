import re
from datetime import date

DATE_RE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b", re.I)
MONEY_RE = re.compile(r"(?:₹|INR|Rs\.?|USD|\$)\s?[\d,]+(?:\.\d+)?")
ID_RE = re.compile(r"\b[A-Z]{2,8}[-_][A-Z0-9]{2,20}\b")

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def extract_deterministic_entities(text: str) -> list[dict]:
    entities = []
    seen = set()
    for pattern, kind in [(DATE_RE, "DATE"), (MONEY_RE, "AMOUNT"), (ID_RE, "ID")]:
        for match in pattern.findall(text):
            key = (kind, match)
            if key not in seen:
                entities.append({"type": kind, "value": match})
                seen.add(key)
    return entities

def sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [c.strip() for c in chunks if len(c.strip()) >= 12]

def normalized_source(source_id: str, source_type: str, text: str, metadata: dict) -> dict:
    clean = normalize_text(text)
    return {
        "source_id": source_id,
        "source_type": source_type,
        "entities": extract_deterministic_entities(clean),
        "claims": sentences(clean),
        "facts": [],
        "dates": DATE_RE.findall(clean),
        "numbers": re.findall(r"\b\d+(?:\.\d+)?\b", clean),
        "locations": [],
        "organizations": [],
        "raw_text": clean,
        "metadata": metadata,
    }
