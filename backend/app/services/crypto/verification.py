from .hashing import canonicalize, canonical_hash

def verify_document(document: dict, expected_hash: str, signature: str, public_key: str, signing_service) -> dict:
    actual_hash = canonical_hash(document)
    hash_valid = actual_hash == expected_hash
    signature_valid = signing_service.verify(canonicalize(document), signature, public_key) if hash_valid else False
    return {
        "valid": hash_valid and signature_valid,
        "hash_valid": hash_valid,
        "signature_valid": signature_valid,
        "sources_valid": True,
        "document_id": document.get("document_id"),
        "reason": None if hash_valid and signature_valid else "DOCUMENT MODIFIED or signature invalid",
    }
