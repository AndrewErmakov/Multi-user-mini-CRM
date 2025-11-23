from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_organization, get_current_user
from app.database.session import get_db
from app.schemas import ContactCreate, ContactListResponse, ContactResponse
from app.schemas.dto import ContactCreateDTO
from app.services import ContactService

router = APIRouter()


@router.get("/", response_model=ContactListResponse)
async def get_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    search: str = Query(None),
    owner_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    org_context=Depends(get_current_organization),
):
    contact_service = ContactService(db)
    result = await contact_service.get_contacts(
        organization_id=org_context["organization_id"],
        page=page,
        page_size=page_size,
        search=search,
        owner_id=owner_id,
        current_user_id=current_user.id,
        user_role=org_context["user_role"],
    )
    return result


@router.post("/", response_model=ContactResponse)
async def create_contact(
    contact_data: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    org_context=Depends(get_current_organization),
):
    contact_service = ContactService(db)

    contact_dto = ContactCreateDTO(
        **contact_data.model_dump(),
        organization_id=org_context["organization_id"],
        owner_id=current_user.id,
    )

    contact = await contact_service.create_contact(contact_dto)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    org_context=Depends(get_current_organization),
):
    contact_service = ContactService(db)
    await contact_service.delete_contact(contact_id, org_context["organization_id"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)
