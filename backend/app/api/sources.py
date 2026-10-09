import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Source
from ..schemas.common import TextSourceRequest, URLSourceRequest
from ..schemas.source import SourceResponse, SourceDetail
from ..config import get_settings
from ..utils.files import safe_filename, validate_extension
from ..utils.validators import validate_url
from ..services.ingestion import extract_file, extract_web, IngestionError
from ..services.crypto.hashing import sha256_text
from ..services.audit.logger import audit

router = APIRouter(prefix="/api/sources", tags=["sources"])

def _next_source_id(db: Session) -> str:
    count = db.query(Source).count() + 1
    while db.query(Source).filter(Source.source_id == f"SRC-{count:03d}").first():
        count += 1
    return f"SRC-{count:03d}"

def _save_source(db, name, source_type, content, metadata=None, filename=None, url=None, classification="INTERNAL", processing_status="PROCESSED"):
    sid = _next_source_id(db)
    source_metadata = dict(metadata or {})
    source_metadata["classification"] = classification
    row = Source(source_id=sid, name=name, source_type=source_type, original_filename=filename, url=url, content=content, content_hash=sha256_text(content), metadata_json=source_metadata, processing_status=processing_status)
    db.add(row)
    db.commit()
    audit(db, "SOURCE_PROCESSED", source_id=sid, details=f"type={source_type}; sha256={row.content_hash}")
    return row

@router.post("/upload", response_model=list[SourceResponse])
async def upload(files: list[UploadFile] = File(...), classification: str = Form("INTERNAL"), db: Session = Depends(get_db)):
    settings = get_settings()
    if classification not in {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}:
        raise HTTPException(status_code=422, detail="Invalid source classification")
    results = []
    for upload in files:
        filename = safe_filename(upload.filename or "upload")
        try:
            validate_extension(filename)
            data = await upload.read()
            if len(data) > settings.max_upload_size:
                raise HTTPException(status_code=413, detail=f"File too large: {filename}")
            path = Path(settings.upload_dir) / f"{uuid.uuid4().hex}_{filename}"
            path.write_bytes(data)
            extracted = extract_file(str(path))
            status = "NEEDS_OCR" if Path(filename).suffix.lower() == ".pdf" and extracted.metadata.get("pages_without_text") and extracted.metadata.get("ocr_status") == "unavailable" else "PROCESSED"
            row = _save_source(db, filename, Path(filename).suffix.lower().lstrip("."), extracted.text, extracted.metadata, filename=filename, classification=classification, processing_status=status)
            if status == "NEEDS_OCR":
                audit(db, "OCR_UNAVAILABLE", source_id=row.source_id, details=f"Scanned PDF could not be OCR-processed: {filename}")
            results.append(row)
        except HTTPException:
            raise
        except (ValueError, IngestionError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        finally:
            try:
                path.unlink()
            except Exception:
                pass
    return results

@router.post("/url", response_model=SourceResponse)
def add_url(request: URLSourceRequest, db: Session = Depends(get_db)):
    try:
        url = validate_url(request.url)
        extracted = extract_web(url)
        return _save_source(db, url, "url", extracted.text, extracted.metadata, url=url, classification=request.classification)
    except (ValueError, IngestionError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.post("/text", response_model=SourceResponse)
def add_text(request: TextSourceRequest, db: Session = Depends(get_db)):
    return _save_source(db, request.name, "text", request.content, {}, classification=request.classification)

@router.get("", response_model=list[SourceResponse])
def list_sources(db: Session = Depends(get_db)):
    return db.query(Source).order_by(Source.id).all()

@router.delete("/{source_id}")
def delete_source(source_id: str, db: Session = Depends(get_db)):
    row = db.query(Source).filter(Source.source_id == source_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Source not found")
    name = row.name
    audit(db, "SOURCE_DELETED", source_id=source_id, details=f"name={name}; sha256={row.content_hash}")
    db.delete(row)
    db.commit()
    return {"source_id": source_id, "deleted": True}

@router.get("/{source_id}", response_model=SourceDetail)
def get_source(source_id: str, db: Session = Depends(get_db)):
    row = db.query(Source).filter(Source.source_id == source_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Source not found")
    return row
