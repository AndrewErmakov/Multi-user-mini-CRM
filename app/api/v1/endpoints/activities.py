from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_organization, get_current_user
from app.database.session import get_db
from app.schemas import ActivityCreate, ActivityListResponse, ActivityResponse
from app.services import ActivityService

router = APIRouter()


@router.get("/deals/{deal_id}/activities", response_model=ActivityListResponse)
async def get_deal_activities(
    deal_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    org_context=Depends(get_current_organization),
):
    activity_service = ActivityService(db)
    result = await activity_service.get_deal_activities(
        deal_id, org_context["organization_id"], page, page_size
    )
    return result


@router.post("/deals/{deal_id}/activities", response_model=ActivityResponse)
async def create_activity(
    deal_id: int,
    activity_data: ActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    org_context=Depends(get_current_organization),
):
    activity_service = ActivityService(db)
    activity = await activity_service.create_activity(
        deal_id, activity_data.dict(), org_context["organization_id"], current_user.id
    )
    return activity
