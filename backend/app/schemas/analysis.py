from pydantic import BaseModel, Field

class ClaimOutput(BaseModel):
    claim: str
    sources: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    claim_type: str = "fact"
    evidence: list[str] = Field(default_factory=list)
    classification: str = "VERIFIED"

class DuplicateOutput(BaseModel):
    claims: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    reason: str = ""
    classification: str = "DUPLICATE"

class ConflictValue(BaseModel):
    value: str
    source: str

class ConflictOutput(BaseModel):
    field: str
    values: list[ConflictValue] = Field(default_factory=list)
    status: str = "UNRESOLVED"
    reason: str = ""
    classification: str = "CONFLICT"

class EntityOutput(BaseModel):
    type: str
    value: str
    sources: list[str] = Field(default_factory=list)

class DateOutput(BaseModel):
    value: str
    context: str = ""
    sources: list[str] = Field(default_factory=list)

class NumberOutput(BaseModel):
    value: str
    context: str = ""
    sources: list[str] = Field(default_factory=list)

class PredictionOutput(BaseModel):
    prediction: str
    basis: list[str] = Field(default_factory=list)
    confidence: str = "Low"
    caveats: list[str] = Field(default_factory=list)

class AnalysisOutput(BaseModel):
    summary: str = ""
    key_points: list[str] = Field(default_factory=list)
    claims: list[ClaimOutput] = Field(default_factory=list)
    entities: list[EntityOutput] = Field(default_factory=list)
    important_dates: list[DateOutput] = Field(default_factory=list)
    important_numbers: list[NumberOutput] = Field(default_factory=list)
    duplicates: list[DuplicateOutput] = Field(default_factory=list)
    conflicts: list[ConflictOutput] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    source_evidence: list[dict] = Field(default_factory=list)
    ai_assessment: str = ""
    predictions: list[PredictionOutput] = Field(default_factory=list)
    ai_status: str = "COMPLETED"
