from .deduplication import deterministic_duplicates
from .conflicts import deterministic_conflicts
from ...schemas.analysis import AnalysisOutput, DuplicateOutput, ConflictOutput

def reconcile(analysis: AnalysisOutput, normalized_sources: list[dict]) -> AnalysisOutput:
    duplicates = list(analysis.duplicates)
    conflicts = list(analysis.conflicts)
    if not duplicates:
        duplicates = [DuplicateOutput.model_validate(d) for d in deterministic_duplicates([c.model_dump() for c in analysis.claims])]
    if not conflicts:
        conflicts = [ConflictOutput.model_validate(c) for c in deterministic_conflicts(normalized_sources)]
    return AnalysisOutput(
        summary=analysis.summary,
        key_points=analysis.key_points,
        claims=analysis.claims,
        entities=analysis.entities,
        important_dates=analysis.important_dates,
        important_numbers=analysis.important_numbers,
        duplicates=duplicates,
        conflicts=conflicts,
        missing_information=analysis.missing_information,
        source_evidence=analysis.source_evidence,
        ai_assessment=analysis.ai_assessment,
        predictions=analysis.predictions,
        ai_status=analysis.ai_status,
    )
