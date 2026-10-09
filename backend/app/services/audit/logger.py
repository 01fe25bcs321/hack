from sqlalchemy.orm import Session
from ...models import AuditLog

def audit(db: Session, event_type: str, document_id: str | None = None, source_id: str | None = None, details: str = ""):
    row = AuditLog(document_id=document_id, event_type=event_type, source_id=source_id, details=details)
    db.add(row)
    db.commit()
