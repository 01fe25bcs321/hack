from pydantic import BaseModel

class VerificationResult(BaseModel):
    valid: bool
    hash_valid: bool
    signature_valid: bool
    sources_valid: bool
    document_id: str | None = None
    reason: str | None = None
