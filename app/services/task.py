from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DealNotFoundException,
    PermissionDeniedException,
    TaskDueDateInPastException,
)
from app.repositories import ActivityRepository, DealRepository, TaskRepository
from app.schemas import TaskResponse
from app.schemas.dto import TaskCreateDTO


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_repo = TaskRepository(db)
        self.deal_repo = DealRepository(db)
        self.activity_repo = ActivityRepository(db)

    async def create_task(
        self, task_dto: TaskCreateDTO, current_user_id: int, user_role: str, organization_id: int
    ) -> TaskResponse:
        deal = await self.deal_repo.get(task_dto.deal_id)
        if not deal:
            raise DealNotFoundException("Deal not found")

        if deal.organization_id != organization_id:
            raise DealNotFoundException("Deal not found in your organization")

        if user_role == "member" and deal.owner_id != current_user_id:
            raise PermissionDeniedException("Cannot create task for other users' deals")

        if task_dto.due_date:
            if isinstance(task_dto.due_date, str):
                due_date = datetime.fromisoformat(task_dto.due_date.replace('Z', '+00:00'))
            else:
                due_date = task_dto.due_date

            if due_date < datetime.utcnow():
                raise TaskDueDateInPastException("Due date cannot be in the past")

        task_data = task_dto.model_dump()
        task = await self.task_repo.create(task_data)

        await self.activity_repo.create(
            {
                "deal_id": task_dto.deal_id,
                "author_id": current_user_id,
                "type": "task_created",
                "payload": {"task_id": task.id, "task_title": task.title},
            }
        )

        return TaskResponse(
            id=task.id,
            deal_id=task.deal_id,
            title=task.title,
            description=task.description,
            due_date=task.due_date,
            is_done=task.is_done,
            created_at=task.created_at,
            deal_title=f"Deal {task.deal_id}",
        )

    async def get_tasks(
        self,
        organization_id: int,
        page: int = 1,
        page_size: int = 100,
        deal_id: int | None = None,
        only_open: bool = False,
        due_before: Optional = None,
        due_after: Optional = None,
    ) -> dict:
        skip = (page - 1) * page_size
        tasks = await self.task_repo.get_organization_tasks(
            organization_id, skip, page_size, deal_id, only_open, due_before, due_after
        )
        total = await self.task_repo.count_organization_tasks(
            organization_id, deal_id, only_open, due_before, due_after
        )

        task_responses = [
            TaskResponse(
                id=task.id,
                deal_id=task.deal_id,
                title=task.title,
                description=task.description,
                due_date=task.due_date,
                is_done=task.is_done,
                created_at=task.created_at,
                deal_title=f"Deal {task.deal_id}",
            )
            for task in tasks
        ]

        return {
            "items": task_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
