from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ContactHasActiveDealsException,
    ContactNotFoundException,
    PermissionDeniedException,
)
from app.repositories import ContactRepository, DealRepository
from app.schemas import ContactResponse
from app.schemas.dto import ContactCreateDTO


class ContactService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.contact_repo = ContactRepository(db)
        self.deal_repo = DealRepository(db)

    async def create_contact(self, contact_dto: ContactCreateDTO) -> ContactResponse:
        contact_data = contact_dto.model_dump()
        contact = await self.contact_repo.create(contact_data)

        return ContactResponse(
            id=contact.id,
            organization_id=contact.organization_id,
            owner_id=contact.owner_id,
            name=contact.name,
            email=contact.email,
            phone=contact.phone,
            created_at=contact.created_at,
            owner_name=f"User {contact.owner_id}",
        )

    async def get_contacts(
        self,
        organization_id: int,
        page: int = 1,
        page_size: int = 100,
        search: str | None = None,
        owner_id: int | None = None,
        current_user_id: int = None,
        user_role: str = None,
    ) -> dict:
        if owner_id and owner_id != current_user_id:
            if user_role == "member":
                raise PermissionDeniedException("Cannot filter by other users' contacts")

        if user_role == "member" and owner_id is None:
            owner_id = current_user_id

        skip = (page - 1) * page_size

        contacts = await self.contact_repo.get_organization_contacts(
            organization_id=organization_id,
            skip=skip,
            limit=page_size,
            search=search,
            owner_id=owner_id,
        )

        total = await self.contact_repo.count_organization_contacts(
            organization_id, search, owner_id
        )

        contact_responses = [
            ContactResponse(
                id=contact.id,
                organization_id=contact.organization_id,
                owner_id=contact.owner_id,
                name=contact.name,
                email=contact.email,
                phone=contact.phone,
                created_at=contact.created_at,
                owner_name=f"User {contact.owner_id}",
            )
            for contact in contacts
        ]

        return {
            "items": contact_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    async def delete_contact(self, contact_id: int, organization_id: int) -> bool:
        contact = await self.contact_repo.get_contact_with_organization(contact_id, organization_id)
        if not contact:
            raise ContactNotFoundException("Contact not found")

        deals = await self.deal_repo.get_organization_deals(organization_id)
        deals_with_contact = [deal for deal in deals if deal.contact_id == contact_id]

        if deals_with_contact:
            raise ContactHasActiveDealsException("Cannot delete contact with active deals")

        return await self.contact_repo.delete(contact_id)
