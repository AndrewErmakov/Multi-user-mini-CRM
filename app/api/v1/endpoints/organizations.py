from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.services import OrganizationService

router = APIRouter()


@router.get("/me")
async def get_my_organizations(
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
) -> list[dict[str, Any]]:
    org_service = OrganizationService(db)
    organizations = await org_service.get_user_organizations(current_user.id)
    return organizations
