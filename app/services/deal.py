from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CannotCloseDealWithZeroAmountException,
    DealNotFoundException,
    InvalidDealStageTransitionException,
    PermissionDeniedException,
    ValidationException,
)
from app.repositories import ActivityRepository, ContactRepository, DealRepository
from app.schemas import DealResponse
from app.schemas.dto import DealCreateDTO


class DealService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.deal_repo = DealRepository(db)
        self.contact_repo = ContactRepository(db)
        self.activity_repo = ActivityRepository(db)

    async def create_deal(self, deal_dto: DealCreateDTO) -> DealResponse:
        contact = await self.contact_repo.get_contact_with_organization(
            deal_dto.contact_id, deal_dto.organization_id
        )
        if not contact:
            raise ValidationException("Contact not found in organization")

        deal_data = deal_dto.model_dump()
        deal = await self.deal_repo.create(deal_data)

        await self.activity_repo.create(
            {
                "deal_id": deal.id,
                "author_id": deal_dto.owner_id,
                "type": "system",
                "payload": {"message": "Deal created"},
            }
        )

        return DealResponse(
            id=deal.id,
            organization_id=deal.organization_id,
            contact_id=deal.contact_id,
            owner_id=deal.owner_id,
            title=deal.title,
            amount=deal.amount,
            currency=deal.currency,
            status=deal.status,
            stage=deal.stage,
            description=deal.description,
            created_at=deal.created_at,
            updated_at=deal.updated_at,
            contact_name=f"Contact {deal.contact_id}",
            owner_name=f"User {deal.owner_id}",
        )

    async def update_deal(
        self,
        deal_id: int,
        update_data: dict,
        organization_id: int,
        current_user_id: int,
        user_role: str,
    ) -> DealResponse:
        deal = await self.deal_repo.get_deal_with_organization(deal_id, organization_id)
        if not deal:
            raise DealNotFoundException("Deal not found")

        if user_role == "member" and deal.owner_id != current_user_id:
            raise PermissionDeniedException("Cannot update other users' deals")

        if "status" in update_data:
            new_status = update_data["status"]

            if new_status == "won" and (deal.amount is None or deal.amount <= 0):
                raise CannotCloseDealWithZeroAmountException(
                    "Cannot close deal as won with amount <= 0"
                )

            if new_status != deal.status:
                await self.activity_repo.create(
                    {
                        "deal_id": deal_id,
                        "author_id": current_user_id,
                        "type": "status_changed",
                        "payload": {"old_status": deal.status, "new_status": new_status},
                    }
                )

        if "stage" in update_data:
            new_stage = update_data["stage"]

            if user_role in ("member", "manager"):
                current_stage_index = self._get_stage_index(deal.stage)
                new_stage_index = self._get_stage_index(new_stage)

                if new_stage_index < current_stage_index:
                    raise InvalidDealStageTransitionException("Cannot move stage backwards")

            if new_stage != deal.stage:
                await self.activity_repo.create(
                    {
                        "deal_id": deal_id,
                        "author_id": current_user_id,
                        "type": "stage_changed",
                        "payload": {"old_stage": deal.stage, "new_stage": new_stage},
                    }
                )

        update_data["updated_at"] = datetime.utcnow()
        updated_deal = await self.deal_repo.update(deal_id, update_data)

        return DealResponse(
            id=updated_deal.id,
            organization_id=updated_deal.organization_id,
            contact_id=updated_deal.contact_id,
            owner_id=updated_deal.owner_id,
            title=updated_deal.title,
            amount=updated_deal.amount,
            currency=updated_deal.currency,
            status=updated_deal.status,
            stage=updated_deal.stage,
            description=updated_deal.description,
            created_at=updated_deal.created_at,
            updated_at=updated_deal.updated_at,
            contact_name=f"Contact {updated_deal.contact_id}",
            owner_name=f"User {updated_deal.owner_id}",
        )

    def _get_stage_index(self, stage: str) -> int:
        stages = ["qualification", "proposal", "negotiation", "closed"]
        return stages.index(stage) if stage in stages else -1

    async def get_deals(
        self,
        organization_id: int,
        page: int = 1,
        page_size: int = 100,
        status: list[str] | None = None,
        stage: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        owner_id: int | None = None,
        order_by: str = "created_at",
        order: str = "desc",
        current_user_id: int = None,
        user_role: str = None,
    ) -> dict:
        if owner_id and owner_id != current_user_id:
            if user_role == "member":
                raise PermissionDeniedException("Cannot filter by other users' deals")

        if user_role == "member" and owner_id is None:
            owner_id = current_user_id

        skip = (page - 1) * page_size
        deals = await self.deal_repo.get_organization_deals(
            organization_id,
            skip,
            page_size,
            status,
            stage,
            min_amount,
            max_amount,
            owner_id,
            order_by,
            order,
        )
        total = await self.deal_repo.count_organization_deals(
            organization_id, status, stage, min_amount, max_amount, owner_id
        )

        deal_responses = [
            DealResponse(
                id=deal.id,
                organization_id=deal.organization_id,
                contact_id=deal.contact_id,
                owner_id=deal.owner_id,
                title=deal.title,
                amount=deal.amount,
                currency=deal.currency,
                status=deal.status,
                stage=deal.stage,
                description=deal.description,
                created_at=deal.created_at,
                updated_at=deal.updated_at,
                contact_name=f"Contact {deal.contact_id}",
                owner_name=f"User {deal.owner_id}",
            )
            for deal in deals
        ]

        return {
            "items": deal_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    async def delete_deal(
        self, deal_id: int, organization_id: int, current_user_id: int, user_role: str
    ) -> bool:
        deal = await self.deal_repo.get_deal_with_organization(deal_id, organization_id)
        if not deal:
            raise DealNotFoundException("Deal not found")

        if user_role == "member" and deal.owner_id != current_user_id:
            raise PermissionDeniedException("Cannot delete other users' deals")

        return await self.deal_repo.delete(deal_id)
