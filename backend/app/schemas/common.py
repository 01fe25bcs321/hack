from pydantic import BaseModel, Field
from typing import Literal

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

class TextSourceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    classification: Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"] = "INTERNAL"

class URLSourceRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)
    classification: Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"] = "INTERNAL"
