from fastapi import APIRouter
from ..schemas.common import HealthResponse
router = APIRouter(tags=["health"])

@router.get("/api/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", service="DocFusion AI", version="1.0.0")
