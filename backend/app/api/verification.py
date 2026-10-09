import json
import shutil
from copy import deepcopy
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends, Form
from sqlalchemy.orm import Session
from ..config import get_settings
from ..database import get_db
from ..models import Document, Signature, VerificationChange, Claim, Conflict, Provenance
from ..services.crypto.hashing import canonicalize, canonical_hash
from ..services.crypto.signing import SigningService
from ..services.audit.logger import audit
from ..services.documents.pdf_generator import write_pdf
from ..services.documents.json_generator import write_json

router = APIRouter(prefix="/api", tags=["verification"])


def _clean(data):
    data = deepcopy(data)
    for key in ("document_hash", "signature", "public_key", "signature_algorithm"):
        data.pop(key, None)
    return data


def _comparison_payload(data):
    data = _clean(data)
    for key in ("document_id", "version", "created_at", "generated_at"):
        data.pop(key, None)
    return data


def _flatten(old, new, path=""):
    changes = []
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(set(old) | set(new)):
            field_path = f"{path}.{key}" if path else key
            if key not in old:
                changes.append((field_path, None, new[key]))
            elif key not in new:
                changes.append((field_path, old[key], None))
            else:
                before, after = old[key], new[key]
                if isinstance(before, dict) and isinstance(after, dict):
                    changes.extend(_flatten(before, after, field_path))
                elif before != after:
                    changes.append((field_path, before, after))
    elif old != new:
        changes.append((path or "document", old, new))
    return changes


def _signature_check(data):
    expected_hash = data.get("document_hash")
    signature = data.get("signature")
    public_key = data.get("public_key")
    if not expected_hash or not signature or not public_key:
        return {"hash_valid": False, "signature_valid": False, "valid": False, "reason": "The candidate is missing its embedded hash or signature material."}
    payload = _clean(data)
    actual_hash = canonical_hash(payload)
    hash_valid = actual_hash == expected_hash
    signer = SigningService(get_settings().key_dir)
    signature_valid = signer.verify(canonicalize(payload), signature, public_key) if hash_valid else False
    return {"hash_valid": hash_valid, "signature_valid": signature_valid, "valid": hash_valid and signature_valid, "actual_hash": actual_hash, "expected_hash": expected_hash, "reason": None if hash_valid and signature_valid else "The content hash or Ed25519 signature does not validate."}


@router.post("/verify")
async def verify(document: UploadFile = File(...), signature: UploadFile | None = File(None), public_key: UploadFile | None = File(None), db: Session = Depends(get_db)):
    try:
        data = json.loads((await document.read()).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Document must be valid JSON: {exc}")
    if signature:
        try:
            sig_data = json.loads((await signature.read()).decode("utf-8"))
            for key in ("document_hash", "signature", "public_key"):
                data.setdefault(key, sig_data.get(key))
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Signature file must be valid JSON: {exc}")
    if public_key:
        data["public_key"] = (await public_key.read()).decode("utf-8")
    result = _signature_check(data)
    audit(db, "DOCUMENT_VERIFIED", data.get("document_id"), details=f"result={'VERIFIED' if result['valid'] else 'FAILED'}; file={document.filename or 'uploaded JSON'}")
    return {**result, "sources_valid": True, "document_id": data.get("document_id"), "file_name": document.filename or "uploaded JSON"}


@router.post("/verify/compare")
async def compare(original_document_id: str = Form(...), document: UploadFile = File(...), db: Session = Depends(get_db)):
    original = db.query(Document).filter(Document.document_id == original_document_id, Document.status == "SIGNED").first()
    if not original:
        raise HTTPException(status_code=404, detail="Trusted signed document not found")
    try:
        candidate = json.loads((await document.read()).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Candidate document must be valid JSON: {exc}")
    if not isinstance(candidate, dict):
        raise HTTPException(status_code=422, detail="Candidate JSON must contain a document object")
    trusted = json.loads(original.canonical_content)
    changes = _flatten(_comparison_payload(trusted), _comparison_payload(candidate))
    signature_result = _signature_check(candidate)
    trusted_signature_row = db.query(Signature).filter(Signature.document_id == original_document_id).first()
    trusted_payload = _clean(trusted)
    trusted_hash_valid = canonical_hash(trusted_payload) == original.document_hash
    trusted_signature_valid = bool(trusted_signature_row and trusted_hash_valid and SigningService(get_settings().key_dir).verify(canonicalize(trusted_payload), trusted_signature_row.signature, trusted_signature_row.public_key))
    trusted_signature_result = {"hash_valid": trusted_hash_valid, "signature_valid": trusted_signature_valid, "valid": trusted_hash_valid and trusted_signature_valid, "algorithm": "Ed25519"}
    signer_matches = bool(trusted_signature_row and candidate.get("public_key") and candidate.get("public_key").strip() == trusted_signature_row.public_key.strip())
    filename = document.filename or "candidate.json"
    rows = []
    for field_path, previous, current in changes:
        section = field_path.split(".")[0].replace("_", " ").title()
        row = VerificationChange(document_id=original_document_id, file_name=filename, section=section, location=field_path, previous_value=json.dumps(previous, ensure_ascii=False), current_value=json.dumps(current, ensure_ascii=False), status="PENDING")
        db.add(row)
        rows.append(row)
    if not changes and (not signature_result["valid"] or not trusted_signature_result["valid"] or not signer_matches):
        row = VerificationChange(document_id=original_document_id, file_name=filename, section="Cryptographic verification", location="document_hash / signature / signer", previous_value=json.dumps({"hash": original.document_hash, "signature_valid": trusted_signature_result["signature_valid"], "trusted_signer": "current trusted signer"}), current_value=json.dumps({"hash_valid": signature_result["hash_valid"], "signature_valid": signature_result["signature_valid"], "signer_matches": signer_matches, "reason": signature_result["reason"] or ("Candidate signing key differs from the trusted signing key." if not signer_matches else None)}), status="PENDING")
        db.add(row)
        rows.append(row)
    db.commit()
    audit(db, "VERIFICATION_COMPARE", original_document_id, details=f"candidate={filename}; differences={len(rows)}; signature_valid={signature_result['valid']}")
    source_names = [source.get("name") for source in trusted.get("sources", []) if isinstance(source, dict) and source.get("name")]
    content_matches = len(changes) == 0
    valid = content_matches and signature_result["valid"] and trusted_signature_result["valid"] and signer_matches
    audit(db, "DOCUMENT_VERIFIED", original_document_id, details=f"result={'VERIFIED' if valid else 'FAILED'}; candidate={filename}; differences={len(rows)}; signer_matches={signer_matches}")
    return {
        "valid": valid,
        "content_matches": content_matches,
        "summary_matches": trusted.get("summary", "") == candidate.get("summary", ""),
        "status": "VERIFIED" if valid else "FAILED",
        "message": "Nothing was tampered with. The candidate content matches the trusted document and its signature is valid." if valid else "Differences or a cryptographic verification failure were found. Review the evidence before deciding.",
        "document_id": original_document_id,
        "trusted_title": original.title,
        "trusted_summary": trusted.get("summary", ""),
        "candidate_file": filename,
        "candidate_title": candidate.get("title", "Untitled document"),
        "candidate_summary": candidate.get("summary", ""),
        "trusted_hash": original.document_hash,
        "candidate_hash": signature_result.get("expected_hash"),
        "signature_check": signature_result,
        "trusted_signature_check": trusted_signature_result,
        "signer_matches": signer_matches,
        "source_files": source_names,
        "changes": [{"id": row.id, "file": row.file_name, "page": "Page/line is unavailable for canonical JSON", "section": row.section, "field_path": row.location, "previous": json.loads(row.previous_value), "current": json.loads(row.current_value), "status": row.status} for row in rows],
        "change_count": len(rows),
    }


@router.post("/verify/decision")
async def decide_comparison(original_document_id: str = Form(...), decision: str = Form(...), document: UploadFile = File(...), db: Session = Depends(get_db)):
    decision = decision.strip().lower()
    if decision not in {"accept", "decline"}:
        raise HTTPException(status_code=422, detail="Decision must be accept or decline")
    original = db.query(Document).filter(Document.document_id == original_document_id, Document.status == "SIGNED").first()
    if not original:
        raise HTTPException(status_code=404, detail="Current trusted document not found")
    try:
        candidate = json.loads((await document.read()).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Candidate document must be valid JSON: {exc}")
    if not isinstance(candidate, dict):
        raise HTTPException(status_code=422, detail="Candidate JSON must contain a document object")
    filename = document.filename or "candidate.json"
    pending = db.query(VerificationChange).filter(VerificationChange.document_id == original_document_id, VerificationChange.file_name == filename, VerificationChange.status == "PENDING").all()
    if decision == "decline":
        for change in pending:
            change.status = "DECLINED"
            change.decided_by = "User"
        db.commit()
        audit(db, "CHANGE_DECLINED", original_document_id, details=f"candidate={filename}; declined_changes={len(pending)}")
        return {"accepted": False, "declined": True, "declined_count": len(pending), "document_id": original_document_id, "message": "Candidate declined. The current trusted document remains unchanged."}

    settings = get_settings()
    old_id = original.document_id
    version = original.version + 1
    root_id = old_id.split("-v")[0]
    new_id = f"{root_id}-v{version}"
    while db.query(Document).filter(Document.document_id == new_id).first():
        version += 1
        new_id = f"{root_id}-v{version}"
    base = _clean(candidate)
    base["document_id"] = new_id
    base["version"] = version
    base["title"] = candidate.get("title") or original.title
    base.pop("signature", None)
    base.pop("public_key", None)
    base.pop("document_hash", None)
    base.pop("signature_algorithm", None)
    digest = canonical_hash(base)
    signer = SigningService(settings.key_dir)
    signature_value = signer.sign(canonicalize(base))
    public_key_value = signer.public_key_pem()
    base["document_hash"] = digest
    base["signature_algorithm"] = "Ed25519"
    new_doc = Document(document_id=new_id, title=base.get("title", original.title), canonical_content=json.dumps(base, ensure_ascii=False, sort_keys=True, separators=(",", ":")), document_hash=digest, version=version, status="SIGNED")
    db.add(new_doc)
    db.flush()
    db.add(Signature(document_id=new_id, algorithm="Ed25519", document_hash=digest, signature=signature_value, public_key=public_key_value))
    for change in pending:
        change.status = "APPROVED"
        change.decided_by = "User"
    db.query(Signature).filter(Signature.document_id == old_id).delete(synchronize_session=False)
    db.query(Claim).filter(Claim.document_id == old_id).delete(synchronize_session=False)
    db.query(Conflict).filter(Conflict.document_id == old_id).delete(synchronize_session=False)
    db.query(Provenance).filter(Provenance.document_id == old_id).delete(synchronize_session=False)
    db.delete(original)
    db.commit()
    full = dict(base)
    full["signature"] = signature_value
    full["public_key"] = public_key_value
    Path(settings.generated_dir).mkdir(parents=True, exist_ok=True)
    write_json(full, str(Path(settings.generated_dir) / f"{new_id}.json"))
    write_pdf(full, str(Path(settings.generated_dir) / f"{new_id}.pdf"))
    for extension in ("json", "pdf"):
        old_path = Path(settings.generated_dir) / f"{old_id}.{extension}"
        if old_path.exists():
            old_path.unlink()
    old_package_dir = Path(settings.verification_dir) / old_id
    if old_package_dir.exists():
        shutil.rmtree(old_package_dir, ignore_errors=True)
    old_package_zip = Path(settings.verification_dir) / f"{old_id}_verification_package.zip"
    if old_package_zip.exists():
        old_package_zip.unlink()
    audit(db, "CHANGE_ACCEPTED", new_id, details=f"superseded={old_id}; candidate={filename}; old document and generated verification files deleted; new hash={digest}")
    return {"accepted": True, "declined": False, "document_id": new_id, "previous_document_deleted": old_id, "version": version, "document_hash": digest, "message": "Candidate accepted, signed as the current trusted document, and the previous document and generated files were deleted."}
