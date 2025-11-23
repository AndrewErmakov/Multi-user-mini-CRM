from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DealNotFoundException,
    PermissionDeniedException,
    TaskDueDateInPastException,
)
from app.schemas.dto import TaskCreateDTO
from app.services import TaskService


@pytest.fixture
def task_dto():
    """Fixture for task DTO"""
    return TaskCreateDTO(
        title="Test Task",
        description="Test description",
        due_date=(datetime.now() + timedelta(days=1)).isoformat(),
        deal_id=1,
    )


@pytest.fixture
def deal():
    """Fixture for deal mock with all required attributes"""
    mock_deal = AsyncMock()
    mock_deal.id = 1
    mock_deal.owner_id = 1
    mock_deal.organization_id = 1
    return mock_deal


@pytest.fixture
def task_service(test_session: AsyncSession):
    """Fixture for TaskService with mocked dependencies"""
    service = TaskService(test_session)
    # Mock repositories
    service.deal_repo = AsyncMock()
    service.task_repo = AsyncMock()
    service.activity_repo = AsyncMock()
    return service


def get_due_date(task_dto):
    """Helper function to safely get due_date from task_dto"""
    if isinstance(task_dto.due_date, str):
        return datetime.fromisoformat(task_dto.due_date.replace('Z', '+00:00'))
    return task_dto.due_date


class TestTaskService:
    @pytest.mark.asyncio
    async def test_create_task_success(self, task_service, task_dto, deal):
        """Test: successful task creation"""
        task_service.deal_repo.get.return_value = deal
        task_service.task_repo.create.return_value = AsyncMock(
            id=1,
            deal_id=1,
            title="Test Task",
            description="Test description",
            due_date=datetime.now() + timedelta(days=1),
            is_done=False,
            created_at=datetime.now(),
        )

        result = await task_service.create_task(
            task_dto,
            current_user_id=1,
            user_role="member",
            organization_id=1
        )

        assert result.id == 1
        assert result.title == "Test Task"
        task_service.deal_repo.get.assert_called_once_with(1)
        task_service.activity_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task_deal_not_found(self, task_service, task_dto):
        """Test: cannot create task for non-existent deal"""
        task_service.deal_repo.get.return_value = None

        with pytest.raises(DealNotFoundException):
            await task_service.create_task(
                task_dto,
                current_user_id=1,
                user_role="member",
                organization_id=1
            )

    @pytest.mark.asyncio
    async def test_create_task_member_cannot_create_for_others_deal(
            self, task_service, task_dto, deal
    ):
        """Test: member cannot create task for other user's deal"""
        # Mock deal owned by different user
        deal.owner_id = 2  # Different owner
        task_service.deal_repo.get.return_value = deal

        with pytest.raises(PermissionDeniedException):
            await task_service.create_task(
                task_dto,
                current_user_id=1,
                user_role="member",
                organization_id=1
            )

    @pytest.mark.asyncio
    async def test_create_task_due_date_in_past(self, task_service, task_dto, deal):
        """Test: cannot create task with due date in the past"""
        task_service.deal_repo.get.return_value = deal

        task_dto.due_date = (datetime.now() - timedelta(days=1)).isoformat()  # Past date

        with pytest.raises(TaskDueDateInPastException):
            await task_service.create_task(
                task_dto,
                current_user_id=1,
                user_role="member",
                organization_id=1
            )

    @pytest.mark.asyncio
    async def test_create_task_deal_from_different_organization(self, task_service, task_dto, deal):
        """Test: cannot create task for deal from different organization"""
        deal.organization_id = 999  # Different organization
        task_service.deal_repo.get.return_value = deal

        with pytest.raises(DealNotFoundException):
            await task_service.create_task(
                task_dto,
                current_user_id=1,  # Исправлено: user_id -> current_user_id
                user_role="admin",
                organization_id=1
            )

    @pytest.mark.asyncio
    async def test_create_task_admin_can_create_for_any_deal_in_organization(self, task_service, task_dto, deal):
        """Test: admin can create task for any deal in organization"""
        # Create deal with different owner but same organization
        deal.owner_id = 999  # Different user
        task_service.deal_repo.get.return_value = deal
        task_service.task_repo.create.return_value = AsyncMock(
            id=1,
            deal_id=1,
            title=task_dto.title,
            description=task_dto.description,
            due_date=get_due_date(task_dto),
            is_done=False,
            created_at=datetime.now(),
        )

        task = await task_service.create_task(
            task_dto,
            current_user_id=1,  # Исправлено: user_id -> current_user_id
            user_role="admin",
            organization_id=1  # Добавлен недостающий параметр
        )

        assert task is not None
        assert task.title == task_dto.title

    @pytest.mark.asyncio
    async def test_create_task_member_can_create_for_own_deal(self, task_service, task_dto, deal):
        """Test: member can create task for their own deal"""
        # Create deal where owner is current user
        deal.owner_id = 1  # Current user
        task_service.deal_repo.get.return_value = deal
        task_service.task_repo.create.return_value = AsyncMock(
            id=1,
            deal_id=1,
            title=task_dto.title,
            description=task_dto.description,
            due_date=get_due_date(task_dto),
            is_done=False,
            created_at=datetime.now(),
        )

        task = await task_service.create_task(
            task_dto,
            current_user_id=1,
            user_role="member",
            organization_id=1
        )

        assert task is not None
        assert task.title == task_dto.title

    @pytest.mark.asyncio
    async def test_create_task_with_nonexistent_deal(self, task_service, task_dto):
        """Test: cannot create task for non-existent deal"""
        task_dto.deal_id = 99999  # Non-existent ID
        task_service.deal_repo.get.return_value = None

        with pytest.raises(DealNotFoundException):
            await task_service.create_task(
                task_dto,
                current_user_id=1,  # Исправлено: user_id -> current_user_id
                user_role="admin",
                organization_id=1
            )

    @pytest.mark.asyncio
    async def test_create_task_manager_can_create_for_any_deal(self, task_service, task_dto, deal):
        """Test: manager can create task for any deal in organization"""
        # Create deal with different owner
        deal.owner_id = 999
        task_service.deal_repo.get.return_value = deal
        task_service.task_repo.create.return_value = AsyncMock(
            id=1,
            deal_id=1,
            title=task_dto.title,
            description=task_dto.description,
            due_date=get_due_date(task_dto),
            is_done=False,
            created_at=datetime.now(),
        )

        task = await task_service.create_task(
            task_dto,
            current_user_id=1,  # Исправлено: user_id -> current_user_id
            user_role="manager",
            organization_id=1  # Добавлен недостающий параметр
        )

        assert task is not None
        assert task.title == task_dto.title

    @pytest.mark.asyncio
    async def test_create_task_deal_same_organization(self, task_service, task_dto, deal):
        """Test: can create task for deal in the same organization"""
        deal.organization_id = 1
        task_service.deal_repo.get.return_value = deal
        task_service.task_repo.create.return_value = AsyncMock(
            id=1,
            deal_id=1,
            title=task_dto.title,
            description=task_dto.description,
            due_date=get_due_date(task_dto),
            is_done=False,
            created_at=datetime.now(),
        )

        task = await task_service.create_task(
            task_dto,
            current_user_id=1,  # Исправлено: user_id -> current_user_id
            user_role="admin",
            organization_id=1
        )

        assert task is not None
        assert task.title == task_dto.title
