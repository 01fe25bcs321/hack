from fastapi import APIRouter, Depends, HTTPException, Query
from time import perf_counter
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Source
from ..schemas.analysis import AnalysisOutput
from ..services.normalization.normalizer import normalized_source
from ..services.ai.gemini import GeminiProvider
from ..services.ai.ollama import OllamaProvider
from ..services.ai.base import AIUnavailable
from ..services.audit.logger import audit
from ..services.fusion.fusion import reconcile
from ..config import get_settings

router = APIRouter(prefix="/api", tags=["analysis"])

@router.get("/ai/providers")
def ai_providers():
    settings = get_settings()
    ollama = OllamaProvider()
    try:
        models = ollama.list_models()
        ollama_status = "connected"
    except AIUnavailable:
        models = []
        ollama_status = "unavailable"
    return {
        "gemini": {"configured": bool(settings.gemini_api_key), "model": settings.gemini_model},
        "ollama": {"status": ollama_status, "base_url": settings.ollama_base_url, "default_model": settings.ollama_model, "models": models},
    }

@router.post("/analyze", response_model=AnalysisOutput)
def analyze(provider: str = Query("gemini", pattern="^(gemini|ollama)$"), model: str | None = Query(None), db: Session = Depends(get_db)):
    sources = db.query(Source).order_by(Source.id).all()
    if not sources:
        raise HTTPException(status_code=400, detail="Add at least one source before analysis")
    normalized = [normalized_source(s.source_id, s.source_type, s.content, s.metadata_json or {}) for s in sources]
    started = perf_counter()
    try:
        ai_provider = GeminiProvider() if provider == "gemini" else OllamaProvider(model=model)
        result = reconcile(ai_provider.analyze_sources(normalized), normalized)
        elapsed = perf_counter() - started
        audit(db, "AI_ANALYSIS_COMPLETED", details=f"mode={'Public AI' if provider == 'gemini' else 'Private AI'}; model={model or 'default'}; sources={len(sources)}; duration_seconds={elapsed:.2f}")
        return result
    except AIUnavailable as exc:
        elapsed = perf_counter() - started
        audit(db, "AI_ANALYSIS_FAILED", details=f"provider={provider}; duration_seconds={elapsed:.2f}: {exc}")
        raise HTTPException(status_code=503, detail=f"AI_ANALYSIS_UNAVAILABLE ({provider}): {exc}") from exc
