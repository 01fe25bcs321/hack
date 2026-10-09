from ...services.crypto.hashing import canonicalize, canonical_hash

def build_canonical_document(document_id: str, version: int, title: str, created_at: str, sources: list[dict], summary: str, claims: list[dict], conflicts: list[dict], provenance: list[dict], missing_information: list[str], ai_status: str, key_points=None, entities=None, important_dates=None, important_numbers=None, duplicates=None, source_evidence=None, ai_assessment="", predictions=None) -> dict:
    return {
        "document_id": document_id,
        "version": version,
        "title": title,
        "created_at": created_at,
        "source_count": len(sources),
        "ai_status": ai_status,
        "summary": summary,
        "key_points": key_points or [],
        "entities": entities or [],
        "important_dates": important_dates or [],
        "important_numbers": important_numbers or [],
        "duplicates": duplicates or [],
        "source_evidence": source_evidence or [],
        "ai_assessment": ai_assessment,
        "predictions": predictions or [],
        "sources": sorted(sources, key=lambda x: x["source_id"]),
        "claims": sorted(claims, key=lambda x: (x.get("claim", ""), x.get("sources", []))),
        "conflicts": sorted(conflicts, key=lambda x: (x.get("field", ""), str(x.get("values", [])))),
        "provenance": sorted(provenance, key=lambda x: (x.get("source_id", ""), x.get("claim", ""))),
        "missing_information": sorted(missing_information),
    }

def hash_document(document: dict) -> tuple[bytes, str]:
    data = canonicalize(document)
    return data, canonical_hash(document)
