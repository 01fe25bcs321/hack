from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal
from .analysis import AnalysisOutput, ClaimOutput, ConflictOutput, EntityOutput, DateOutput, NumberOutput, DuplicateOutput, PredictionOutput

class DocumentResponse(BaseModel):
    document_id: str
    title: str
    version: int
    created_at: datetime
    status: str
    document_hash: str
    summary: str
    source_count: int
    ai_status: str
    classification: str = "INTERNAL"
    redaction_count: int = 0
    key_points: list[str] = []
    claims: list[ClaimOutput] = []
    entities: list[EntityOutput] = []
    important_dates: list[DateOutput] = []
    important_numbers: list[NumberOutput] = []
    duplicates: list[DuplicateOutput] = []
    conflicts: list[ConflictOutput] = []
    provenance: list[dict] = []
    source_evidence: list[dict] = []
    ai_assessment: str = ""
    predictions: list[PredictionOutput] = []
    signature: dict | None = None

class GenerateDocumentRequest(BaseModel):
    title: str = Field(default="DocFusion AI Report", min_length=1, max_length=255)
    output_classification: Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"] = "INTERNAL"
    analysis: AnalysisOutput
