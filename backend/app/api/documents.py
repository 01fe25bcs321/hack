import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Document, Source, Claim, Conflict, Provenance, Signature
from ..schemas.analysis import AnalysisOutput
from ..schemas.document import DocumentResponse, GenerateDocumentRequest
from ..config import get_settings
from ..services.documents.manager import DocumentManager
from ..services.audit.logger import audit

router = APIRouter(prefix="/api/documents", tags=["documents"])

def _next_document_id(db: Session) -> str:
    from datetime import datetime
    year = datetime.now().year
    count = db.query(Document).count() + 1
    return f"DF-{year}-{count:04d}"

@router.get("", tags=["documents"])
def list_documents(db: Session = Depends(get_db)):
    rows = db.query(Document).filter(Document.status == "SIGNED").order_by(Document.created_at.desc()).all()
    result = []
    for row in rows:
        try:
            content = json.loads(row.canonical_content)
        except Exception:
            content = {}
        result.append({"document_id": row.document_id, "title": row.title, "version": row.version, "status": row.status, "created_at": row.created_at.isoformat(), "document_hash": row.document_hash, "summary": content.get("summary", ""), "source_count": content.get("source_count", 0)})
    return {"documents": result}

@router.post("/generate", response_model=DocumentResponse)
def generate(request: GenerateDocumentRequest, db: Session = Depends(get_db)):
    analysis = request.analysis
    sources = db.query(Source).order_by(Source.id).all()
    hierarchy = {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}
    output_level = hierarchy.get(request.output_classification, 1)
    higher_class_sources = [source.name for source in sources if hierarchy.get((source.metadata_json or {}).get("classification", "INTERNAL"), 1) > output_level and (source.metadata_json or {}).get("classification", "INTERNAL") in {"CONFIDENTIAL", "RESTRICTED"}]
    if higher_class_sources:
        raise HTTPException(status_code=422, detail="Output classification is lower than one or more confidential/restricted sources. Choose an appropriate output classification or remove those sources before generating.")
    document_id = _next_document_id(db)
    manager = DocumentManager(db, get_settings())
    doc = manager.generate(request.title, analysis, sources, document_id, 1, request.output_classification)
    audit(db, "DOCUMENT_GENERATED", document_id, details="Signed document generated")
    return get_document(document_id, db)

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    canonical = json.loads(doc.canonical_content)
    sig = db.query(Signature).filter(Signature.document_id == document_id).first()
    return DocumentResponse(document_id=doc.document_id, title=doc.title, version=doc.version, created_at=doc.created_at, status=doc.status, document_hash=doc.document_hash, summary=canonical.get("summary", ""), source_count=canonical.get("source_count", 0), ai_status=canonical.get("ai_status", ""), classification=canonical.get("classification", "INTERNAL"), redaction_count=canonical.get("redaction_count", 0), key_points=canonical.get("key_points", []), claims=canonical.get("claims", []), entities=canonical.get("entities", []), important_dates=canonical.get("important_dates", []), important_numbers=canonical.get("important_numbers", []), duplicates=canonical.get("duplicates", []), conflicts=canonical.get("conflicts", []), provenance=canonical.get("provenance", []), source_evidence=canonical.get("source_evidence", []), ai_assessment=canonical.get("ai_assessment", ""), predictions=canonical.get("predictions", []), signature={"algorithm": sig.algorithm, "signature": sig.signature, "public_key": sig.public_key} if sig else None)

@router.get("/{document_id}/download")
def download(document_id: str, format: str = "pdf", db: Session = Depends(get_db)):
    settings = get_settings()
    audit(db, "DOCUMENT_DOWNLOADED", document_id, details=f"format={format}")
    if format not in {"pdf", "json"}:
        raise HTTPException(status_code=422, detail="format must be pdf or json")
    path = Path(settings.generated_dir) / f"{document_id}.{format}"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Generated document not found")
    return FileResponse(path, filename=path.name)

@router.get("/{document_id}/verification-package")
def verification_package(document_id: str, db: Session = Depends(get_db)):
    import zipfile
    settings = get_settings()
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    sig = db.query(Signature).filter(Signature.document_id == document_id).first()
    if not doc or not sig:
        raise HTTPException(status_code=404, detail="Document or signature not found")
    out_dir = Path(settings.verification_dir) / document_id
    out_dir.mkdir(parents=True, exist_ok=True)
    canonical = json.loads(doc.canonical_content)
    (out_dir / "document.json").write_text(json.dumps(canonical, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "signature.json").write_text(json.dumps({"algorithm": sig.algorithm, "document_hash": sig.document_hash, "signature": sig.signature, "public_key": sig.public_key}, indent=2), encoding="utf-8")
    sources = db.query(Source).all()
    manifest = {"document_id": document_id, "version": doc.version, "hash_algorithm": "SHA-256", "document_hash": doc.document_hash, "signature_algorithm": sig.algorithm, "signature": sig.signature, "public_key": sig.public_key, "sources": [{"source_id": s.source_id, "sha256": s.content_hash} for s in sources]}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out_dir / "source_manifest.json").write_text(json.dumps(manifest["sources"], indent=2), encoding="utf-8")
    pdf = Path(settings.generated_dir) / f"{document_id}.pdf"
    if pdf.exists():
        import shutil
        shutil.copy2(pdf, out_dir / "document.pdf")
    zip_path = Path(settings.verification_dir) / f"{document_id}_verification_package.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in out_dir.iterdir():
            z.write(p, p.name)
    audit(db, "VERIFICATION_PACKAGE_GENERATED", document_id)
    return FileResponse(zip_path, filename=zip_path.name, media_type="application/zip")
