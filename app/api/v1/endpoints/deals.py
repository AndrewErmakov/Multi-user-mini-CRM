from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_organization, get_current_user
from app.database.session import get_db
from app.schemas import DealCreate, DealListResponse, DealResponse, DealUpdate
from app.schemas.dto import DealCreateDTO
from app.services import DealService

router = APIRouter()


@router.get("/", response_model=DealListResponse)
async def get_deals(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    status: list[str] | None = Query(None),
    stage: str | None = Query(None),
    min_amount: float | None = Query(None),
    max_amount: float | None = Query(None),
    owner_id: int | None = Query(None),
    order_by: str = Query("created_at", regex="^(created_at|amount)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    org_context=Depends(get_current_organization),
):
    deal_service = DealService(db)
    result = await deal_service.get_deals(
        organization_id=org_context["organization_id"],
        page=page,
        page_size=page_size,
        status=status,
        stage=stage,
        min_amount=min_amount,
        max_amount=max_amount,
        owner_id=owner_id,
        order_by=order_by,
        order=order,
        current_user_id=current_user.id,
        user_role=org_context["user_role"],
    )
    return result


@router.post("/", response_model=DealResponse)
async def create_deal(
    deal_data: DealCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    org_context=Depends(get_current_organization),
):
    deal_service = DealService(db)

    deal_dto = DealCreateDTO(
        **deal_data.model_dump(),
        organization_id=org_context["organization_id"],
        owner_id=current_user.id,
    )

    deal = await deal_service.create_deal(deal_dto)
    return deal


@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: int,
    deal_update: DealUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    org_context=Depends(get_current_organization),
):
    deal_service = DealService(db)
    deal = await deal_service.update_deal(
        deal_id,
        deal_update.model_dump(exclude_unset=True),
        org_context["organization_id"],
        current_user.id,
        org_context["user_role"],
    )
    return deal


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    org_context=Depends(get_current_organization),
):
    deal_service = DealService(db)
    await deal_service.delete_deal(
        deal_id, org_context["organization_id"], current_user.id, org_context["user_role"]
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
