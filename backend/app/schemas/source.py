from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    source_id: str
    name: str
    source_type: str
    original_filename: str | None = None
    url: str | None = None
    content_hash: str
    metadata: dict = Field(default_factory=dict, validation_alias="metadata_json")
    created_at: datetime
    processing_status: str

class SourceDetail(SourceResponse):
    content: str
