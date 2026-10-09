from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Source, Document, AuditLog, VerificationChange
from ..config import get_settings

router = APIRouter(prefix='/api/dashboard', tags=['dashboard'])

@router.get('')
def dashboard(db: Session = Depends(get_db)):
    import json
    sources = db.query(Source).order_by(Source.created_at.desc()).all()
    documents = db.query(Document).order_by(Document.created_at.desc()).limit(8).all()
    audits = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(8).all()
    settings = get_settings()
    gemini_status = {'configured': bool(settings.gemini_api_key), 'model': settings.gemini_model}
    try:
        import requests
        response = requests.get(f'{settings.ollama_base_url.rstrip("/")}/api/tags', timeout=2)
        response.raise_for_status()
        models = [m.get('name') for m in response.json().get('models', []) if m.get('name')]
        ollama_status = {'status': 'connected', 'model_count': len(models), 'models': models}
    except Exception:
        ollama_status = {'status': 'unavailable', 'model_count': 0, 'models': []}
    type_counts = {}
    for source in sources:
        type_counts[source.source_type] = type_counts.get(source.source_type, 0) + 1
    all_documents = db.query(Document).all()
    payloads = []
    for document in all_documents:
        try:
            payloads.append(json.loads(document.canonical_content))
        except Exception:
            continue
    claims = [claim for payload in payloads for claim in payload.get('claims', []) if isinstance(claim, dict)]
    cited_claims = sum(1 for claim in claims if claim.get('sources'))
    provenance_rows = [row for payload in payloads for row in payload.get('provenance', []) if isinstance(row, dict)]
    provenance_claims = {row.get('claim') for row in provenance_rows if row.get('claim')}
    traceable_claims = sum(1 for claim in claims if claim.get('claim') in provenance_claims)
    unsupported_claims = sum(1 for claim in claims if not claim.get('sources'))
    redactions = sum(int(payload.get('redaction_count', 0) or 0) for payload in payloads)
    classification_counts = {}
    for source in sources:
        classification = (source.metadata_json or {}).get('classification', 'INTERNAL')
        classification_counts[classification] = classification_counts.get(classification, 0) + 1
    ocr_attempted = sum(1 for source in sources if (source.metadata_json or {}).get('ocr_attempted'))
    ocr_succeeded = sum(1 for source in sources if (source.metadata_json or {}).get('ocr_status') == 'completed')
    needs_ocr = sum(1 for source in sources if source.processing_status == 'NEEDS_OCR')
    conflict_rows = [conflict for payload in payloads for conflict in payload.get('conflicts', []) if isinstance(conflict, dict)]
    unresolved = sum(1 for conflict in conflict_rows if str(conflict.get('status', 'UNRESOLVED')).upper() not in {'RESOLVED', 'CONFIRMED', 'ACCEPTED'})
    processed_count = sum(1 for source in sources if source.processing_status == 'PROCESSED')
    completed_analyses = [event for event in db.query(AuditLog).filter(AuditLog.event_type == 'AI_ANALYSIS_COMPLETED').all() if 'duration_seconds=' in (event.details or '')]
    analysis_durations = []
    for event in completed_analyses:
        try:
            token = next(part for part in event.details.split(';') if 'duration_seconds=' in part)
            analysis_durations.append(float(token.split('=', 1)[1]))
        except (StopIteration, ValueError):
            pass
    verified_comparisons = db.query(AuditLog).filter(AuditLog.event_type == 'DOCUMENT_VERIFIED', AuditLog.details.like('%result=VERIFIED%')).count()
    return {
        'stats': {
            'sources': len(sources), 'processed': processed_count, 'documents': len(all_documents),
            'audit_events': db.query(AuditLog).count(), 'claims': len(claims), 'claims_with_citations': cited_claims,
            'citation_coverage_pct': round(100 * cited_claims / len(claims), 1) if claims else 0,
            'conflicts': len(conflict_rows), 'unresolved_conflicts': unresolved,
            'duplicates': sum(len(payload.get('duplicates', [])) for payload in payloads),
            'entities': sum(len(payload.get('entities', [])) for payload in payloads),
            'dates': sum(len(payload.get('important_dates', [])) for payload in payloads),
            'provenance_records': len(provenance_rows),
            'provenance_coverage_pct': round(100 * traceable_claims / len(claims), 1) if claims else 0,
            'unsupported_claims': unsupported_claims,
            'unsupported_claim_pct': round(100 * unsupported_claims / len(claims), 1) if claims else 0,
            'redactions': redactions,
            'ocr_attempted': ocr_attempted,
            'ocr_succeeded': ocr_succeeded,
            'ocr_success_pct': round(100 * ocr_succeeded / ocr_attempted, 1) if ocr_attempted else 0,
            'needs_ocr': needs_ocr,
            'classification_counts': classification_counts,
            'extraction_success_pct': round(100 * processed_count / len(sources), 1) if sources else 0,
            'average_analysis_seconds': round(sum(analysis_durations) / len(analysis_durations), 2) if analysis_durations else None,
            'analysis_runs_timed': len(analysis_durations),
        },
        'source_types': type_counts,
        'recent_sources': [{'source_id': source.source_id, 'name': source.name, 'type': source.source_type, 'status': source.processing_status, 'hash': source.content_hash[:16], 'created_at': source.created_at.isoformat()} for source in sources[:8]],
        'recent_documents': [{'document_id': document.document_id, 'title': document.title, 'status': document.status, 'hash': document.document_hash[:16], 'created_at': document.created_at.isoformat()} for document in documents],
        'audit': [{'event': event.event_type, 'source_id': event.source_id, 'document_id': event.document_id, 'timestamp': event.timestamp.isoformat(), 'details': event.details} for event in audits],
        'providers': {'gemini': gemini_status, 'ollama': ollama_status},
        'verification': {'verified': verified_comparisons, 'failed': db.query(VerificationChange).filter(VerificationChange.status == 'PENDING').count(), 'approved': db.query(VerificationChange).filter(VerificationChange.status == 'APPROVED').count(), 'declined': db.query(VerificationChange).filter(VerificationChange.status == 'DECLINED').count()},
    }
