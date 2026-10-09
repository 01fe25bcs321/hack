import json
import re
from pathlib import Path
from sqlalchemy.orm import Session
from ...models import Document, Claim, Conflict, Provenance, Signature, Source
from ...services.crypto.hashing import canonicalize, canonical_hash
from ...services.crypto.signing import SigningService
from ...services.documents.canonical import build_canonical_document
from ...services.documents.json_generator import write_json
from ...services.documents.pdf_generator import write_pdf
from ...services.audit.logger import audit
from ...utils.timestamps import utc_now

class DocumentManager:
    def __init__(self, db: Session, settings):
        self.db = db
        self.settings = settings
        self.signer = SigningService(settings.key_dir)

    def generate(self, title: str, analysis, sources: list[Source], document_id: str, version: int = 1, output_classification: str = "INTERNAL") -> Document:
        created = utc_now()
        provenance = []
        claims_payload = []
        for c in analysis.claims:
            payload = c.model_dump()
            claims_payload.append(payload)
        for c in claims_payload:
            for sid in c.get("sources", []):
                evidence = ""
                source = next((s for s in sources if s.source_id == sid), None)
                if source:
                    evidence = self._find_evidence(source.content, c["claim"])
                provenance.append({"claim": c["claim"], "source_id": sid, "evidence": evidence})

        source_payload = [{"source_id": s.source_id, "name": s.name, "source_type": s.source_type, "content_hash": s.content_hash, "classification": (s.metadata_json or {}).get("classification", "INTERNAL")} for s in sources]
        conflicts_payload = [c.model_dump() for c in analysis.conflicts]
        canonical = build_canonical_document(document_id, version, title, created.isoformat(), source_payload, analysis.summary, claims_payload, conflicts_payload, provenance, analysis.missing_information, analysis.ai_status, analysis.key_points, [e.model_dump() for e in analysis.entities], [d.model_dump() for d in analysis.important_dates], [n.model_dump() for n in analysis.important_numbers], [d.model_dump() for d in analysis.duplicates], analysis.source_evidence, analysis.ai_assessment, [p.model_dump() for p in analysis.predictions])
        canonical["classification"] = output_classification
        redaction_count = 0
        if output_classification == "PUBLIC":
            canonical, redaction_count = self._redact_public(canonical)
        canonical["redaction_count"] = redaction_count
        raw = canonicalize(canonical)
        digest = canonical_hash(canonical)
        signature = self.signer.sign(raw)
        canonical["document_hash"] = digest
        canonical["signature_algorithm"] = "Ed25519"

        doc = Document(document_id=document_id, title=title, canonical_content=json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")), document_hash=digest, version=version, created_at=created, status="SIGNED")
        self.db.add(doc)
        for c in analysis.claims:
            row = Claim(document_id=document_id, claim=c.claim, claim_type=c.claim_type, confidence=c.confidence)
            self.db.add(row)
            self.db.flush()
            for sid in c.sources:
                evidence = next((p["evidence"] for p in provenance if p["claim"] == c.claim and p["source_id"] == sid), "")
                self.db.add(Provenance(document_id=document_id, claim_id=row.id, source_id=sid, evidence=evidence))
        for c in analysis.conflicts:
            values = c.values
            if len(values) >= 2:
                self.db.add(Conflict(document_id=document_id, field=c.field, source_a=values[0].source, value_a=values[0].value, source_b=values[1].source, value_b=values[1].value, resolution=None, status=c.status.upper(), reason=c.reason))
        self.db.add(Signature(document_id=document_id, algorithm="Ed25519", document_hash=digest, signature=signature, public_key=self.signer.public_key_pem()))
        self.db.commit()

        full_document = dict(canonical)
        full_document["signature"] = signature
        full_document["public_key"] = self.signer.public_key_pem()
        json_path = Path(self.settings.generated_dir) / f"{document_id}.json"
        pdf_path = Path(self.settings.generated_dir) / f"{document_id}.pdf"
        write_json(full_document, str(json_path))
        pdf_document = dict(full_document)
        write_pdf(pdf_document, str(pdf_path))
        audit(self.db, "DOCUMENT_GENERATED", document_id, details=f"SHA-256={digest}; version={version}")
        return doc

    @staticmethod
    def _redact_public(value):
        patterns = [
            (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[REDACTED_EMAIL]"),
            (re.compile(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"), "[REDACTED_PHONE]"),
            (re.compile(r"\b(?:EMP(?:LOYEE)?\s*ID|STAFF\s*ID)\s*[:#-]?\s*[A-Z0-9-]{3,}\b", re.I), "[REDACTED_EMPLOYEE_ID]"),
            (re.compile(r"(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)"), "[REDACTED_ID_NUMBER]"),
        ]
        count = 0
        def walk(item):
            nonlocal count
            if isinstance(item, str):
                for pattern, replacement in patterns:
                    item, hits = pattern.subn(replacement, item)
                    count += hits
                return item
            if isinstance(item, list):
                return [walk(child) for child in item]
            if isinstance(item, dict):
                return {key: walk(child) for key, child in item.items()}
            return item
        return walk(value), count

    @staticmethod
    def _find_evidence(content: str, claim: str) -> str:
        claim_words = [w.lower() for w in claim.split() if len(w) > 4]
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            return content[:500]
        best = max(lines, key=lambda line: sum(w in line.lower() for w in claim_words))
        return best[:1000]
