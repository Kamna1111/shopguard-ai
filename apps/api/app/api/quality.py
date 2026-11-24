"""Read-only quality dashboard API."""

from fastapi import APIRouter

from app.domain.schemas import QualityDashboardRead
from app.services.quality_dashboard import build_quality_dashboard

router = APIRouter(prefix="/quality", tags=["Quality dashboard"])


@router.get("/summary", response_model=QualityDashboardRead)
def quality_summary() -> QualityDashboardRead:
    """Return safe summaries from saved browser, API, AI, and performance checks."""
    return build_quality_dashboard()
