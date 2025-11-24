from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_organization
from app.database.session import get_db
from app.schemas import DealFunnelResponse, DealSummaryResponse
from app.services import AnalyticsService

router = APIRouter()


@router.get("/deals/summary", response_model=DealSummaryResponse)
async def get_deal_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days for new deals period"),
    db: AsyncSession = Depends(get_db),
    org_context=Depends(get_current_organization),
):
    analytics_service = AnalyticsService(db)
    summary = await analytics_service.get_deal_summary(org_context["organization_id"], days=days)
    return summary


@router.get("/deals/funnel", response_model=DealFunnelResponse)
async def get_deal_funnel(
    db: AsyncSession = Depends(get_db), org_context=Depends(get_current_organization)
):
    analytics_service = AnalyticsService(db)
    funnel = await analytics_service.get_deal_funnel(org_context["organization_id"])
    return funnel
