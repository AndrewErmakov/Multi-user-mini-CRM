from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ContactHasActiveDealsException,
    ContactNotFoundException,
    PermissionDeniedException,
)
from app.schemas import ContactResponse
from app.schemas.dto import ContactCreateDTO
from app.services import ContactService


class TestContactService:
    @pytest.mark.asyncio
    async def test_create_contact_success(self):
        mock_db = AsyncMock(spec=AsyncSession)
        contact_service = ContactService(mock_db)

        # Создаем реалистичный мок контакта
        mock_contact = MagicMock()
        mock_contact.id = 1
        mock_contact.organization_id = 1
        mock_contact.owner_id = 1
        mock_contact.name = "Test Contact"
        mock_contact.email = "test@example.com"
        mock_contact.phone = "+1234567890"
        mock_contact.created_at = "2023-01-01T00:00:00"

        # Mock repositories
        contact_service.contact_repo = AsyncMock()
        contact_service.contact_repo.create = AsyncMock(return_value=mock_contact)

        contact_dto = ContactCreateDTO(
            name="Test Contact",
            email="test@example.com",
            phone="+1234567890",
            organization_id=1,
            owner_id=1,
        )

        result = await contact_service.create_contact(contact_dto)

        # Проверяем что метод репозитория был вызван с правильными данными
        contact_service.contact_repo.create.assert_called_once()

        # Проверяем что возвращается правильный ContactResponse
        assert isinstance(result, ContactResponse)
        assert result.id == 1
        assert result.name == "Test Contact"
        assert result.email == "test@example.com"
        assert result.phone == "+1234567890"
        assert result.organization_id == 1
        assert result.owner_id == 1

    @pytest.mark.asyncio
    async def test_get_contacts_member_cannot_filter_others(self):
        mock_db = AsyncMock(spec=AsyncSession)
        contact_service = ContactService(mock_db)

        with pytest.raises(PermissionDeniedException):
            await contact_service.get_contacts(
                organization_id=1,
                owner_id=2,  # Different user ID
                current_user_id=1,
                user_role="member",
            )

    @pytest.mark.asyncio
    async def test_get_contacts_member_default_own_contacts(self):
        mock_db = AsyncMock(spec=AsyncSession)
        contact_service = ContactService(mock_db)

        # Mock repositories
        contact_service.contact_repo = AsyncMock()
        contact_service.contact_repo.get_organization_contacts = AsyncMock(return_value=[])
        contact_service.contact_repo.count_organization_contacts = AsyncMock(return_value=0)

        await contact_service.get_contacts(organization_id=1, current_user_id=1, user_role="member")

        # Should call with owner_id=1 (current user)
        contact_service.contact_repo.get_organization_contacts.assert_called_once()
        call_args = contact_service.contact_repo.get_organization_contacts.call_args

        # Проверяем ИМЕНОВАННЫЕ аргументы (а не позиционные)
        kwargs = call_args.kwargs

        # Проверяем что owner_id=1 был передан
        assert "owner_id" in kwargs
        assert kwargs["owner_id"] == 1  # owner_id должен быть равен 1 (current user)

        # Дополнительные проверки других параметров
        assert kwargs["organization_id"] == 1
        assert kwargs["skip"] == 0  # page=1, skip = (1-1)*100 = 0
        assert kwargs["limit"] == 100  # page_size=100
        assert kwargs["search"] is None

    @pytest.mark.asyncio
    async def test_delete_contact_not_found(self):
        mock_db = AsyncMock(spec=AsyncSession)
        contact_service = ContactService(mock_db)

        contact_service.contact_repo = AsyncMock()
        contact_service.contact_repo.get_contact_with_organization = AsyncMock(return_value=None)

        with pytest.raises(ContactNotFoundException):
            await contact_service.delete_contact(1, 1)

    @pytest.mark.asyncio
    async def test_delete_contact_with_active_deals(self):
        mock_db = AsyncMock(spec=AsyncSession)
        contact_service = ContactService(mock_db)

        # Mock contact exists
        contact_service.contact_repo = AsyncMock()
        contact_service.contact_repo.get_contact_with_organization = AsyncMock(
            return_value=MagicMock(id=1, organization_id=1)
        )

        # Mock deals exist for this contact
        contact_service.deal_repo = AsyncMock()
        mock_deal = MagicMock(contact_id=1)
        contact_service.deal_repo.get_organization_deals = AsyncMock(return_value=[mock_deal])

        with pytest.raises(ContactHasActiveDealsException):
            await contact_service.delete_contact(1, 1)
