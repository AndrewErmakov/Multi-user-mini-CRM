from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CannotCloseDealWithZeroAmountException,
    DealNotFoundException,
    InvalidDealStageTransitionException,
    PermissionDeniedException,
    ValidationException,
)
from app.schemas.dto import DealCreateDTO
from app.services import DealService


class TestDealService:
    @pytest.mark.asyncio
    async def test_create_deal_success(self, test_session: AsyncSession):
        deal_service = DealService(test_session)

        # Mock repositories
        deal_service.contact_repo.get_contact_with_organization = AsyncMock(
            return_value=type("obj", (object,), {"id": 1})
        )
        deal_service.deal_repo.create = AsyncMock()
        deal_service.deal_repo.create.return_value = type(
            "obj",
            (object,),
            {
                "id": 1,
                "organization_id": 1,
                "contact_id": 1,
                "owner_id": 1,
                "title": "Test Deal",
                "amount": Decimal("1000.00"),
                "currency": "USD",
                "status": "new",
                "stage": "qualification",
                "description": "Test description",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": None,
            },
        )
        deal_service.activity_repo.create = AsyncMock()

        deal_dto = DealCreateDTO(
            title="Test Deal",
            contact_id=1,
            organization_id=1,
            owner_id=1,
            amount=Decimal("1000.00"),
            currency="USD",
            status="new",
            stage="qualification",
        )

        result = await deal_service.create_deal(deal_dto)

        assert result.id == 1
        assert result.title == "Test Deal"
        deal_service.contact_repo.get_contact_with_organization.assert_called_once_with(1, 1)
        deal_service.activity_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_deal_contact_not_in_organization(self, test_session: AsyncSession):
        deal_service = DealService(test_session)

        deal_service.contact_repo.get_contact_with_organization = AsyncMock(return_value=None)

        deal_dto = DealCreateDTO(title="Test Deal", contact_id=1, organization_id=1, owner_id=1)

        with pytest.raises(ValidationException):
            await deal_service.create_deal(deal_dto)

    @pytest.mark.asyncio
    async def test_update_deal_not_found(self, test_session: AsyncSession):
        deal_service = DealService(test_session)

        deal_service.deal_repo.get_deal_with_organization = AsyncMock(return_value=None)

        with pytest.raises(DealNotFoundException):
            await deal_service.update_deal(1, {}, 1, 1, "member")

    @pytest.mark.asyncio
    async def test_update_deal_member_cannot_update_others(self, test_session: AsyncSession):
        deal_service = DealService(test_session)

        # Mock deal owned by different user
        mock_deal = type(
            "obj",
            (object,),
            {
                "id": 1,
                "organization_id": 1,
                "owner_id": 2,  # Different owner
                "amount": Decimal("1000.00"),
                "status": "new",
                "stage": "qualification",
            },
        )
        deal_service.deal_repo.get_deal_with_organization = AsyncMock(return_value=mock_deal)

        with pytest.raises(PermissionDeniedException):
            await deal_service.update_deal(1, {}, 1, 1, "member")

    @pytest.mark.asyncio
    async def test_update_deal_cannot_close_with_zero_amount(self, test_session: AsyncSession):
        deal_service = DealService(test_session)

        mock_deal = type(
            "obj",
            (object,),
            {
                "id": 1,
                "organization_id": 1,
                "owner_id": 1,
                "amount": Decimal("0.00"),  # Zero amount
                "status": "new",
                "stage": "qualification",
            },
        )
        deal_service.deal_repo.get_deal_with_organization = AsyncMock(return_value=mock_deal)
        deal_service.activity_repo.create = AsyncMock()

        update_data = {"status": "won"}

        with pytest.raises(CannotCloseDealWithZeroAmountException):
            await deal_service.update_deal(1, update_data, 1, 1, "member")

    @pytest.mark.asyncio
    async def test_update_deal_member_cannot_move_stage_backwards(self, test_session: AsyncSession):
        deal_service = DealService(test_session)

        mock_deal = type(
            "obj",
            (object,),
            {
                "id": 1,
                "organization_id": 1,
                "owner_id": 1,
                "amount": Decimal("1000.00"),
                "status": "new",
                "stage": "negotiation",  # Current stage is negotiation
            },
        )
        deal_service.deal_repo.get_deal_with_organization = AsyncMock(return_value=mock_deal)
        deal_service.activity_repo.create = AsyncMock()

        # Trying to move back to proposal
        update_data = {"stage": "proposal"}

        with pytest.raises(InvalidDealStageTransitionException):
            await deal_service.update_deal(1, update_data, 1, 1, "member")

    @pytest.mark.asyncio
    async def test_get_stage_index(self, test_session: AsyncSession):
        deal_service = DealService(test_session)

        assert deal_service._get_stage_index("qualification") == 0
        assert deal_service._get_stage_index("proposal") == 1
        assert deal_service._get_stage_index("negotiation") == 2
        assert deal_service._get_stage_index("closed") == 3
        assert deal_service._get_stage_index("unknown") == -1
