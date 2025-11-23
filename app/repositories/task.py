from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Task
from .base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db: AsyncSession):
        super().__init__(Task, db)

    async def get_organization_tasks(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
        deal_id: int | None = None,
        only_open: bool = False,
        due_before: Optional = None,
        due_after: Optional = None,
    ) -> list[Task]:
        from app.models.deal import Deal

        query = (
            select(Task)
            .join(Deal, Task.deal_id == Deal.id)
            .where(Deal.organization_id == organization_id) # noqa E712
        )

        if deal_id:
            query = query.where(Task.deal_id == deal_id)

        if only_open:
            query = query.where(Task.is_done == False) # noqa E712

        if due_before:
            query = query.where(Task.due_date <= due_before)

        if due_after:
            query = query.where(Task.due_date >= due_after)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_organization_tasks(
        self,
        organization_id: int,
        deal_id: int | None = None,
        only_open: bool = False,
        due_before: Optional = None,
        due_after: Optional = None,
    ) -> int:
        from app.models.deal import Deal

        query = (
            select(Task)
            .join(Deal, Task.deal_id == Deal.id)
            .where(Deal.organization_id == organization_id)
        )

        if deal_id:
            query = query.where(Task.deal_id == deal_id)

        if only_open:
            query = query.where(Task.is_done == False) # noqa E712

        if due_before:
            query = query.where(Task.due_date <= due_before)

        if due_after:
            query = query.where(Task.due_date >= due_after)

        result = await self.db.execute(query)
        return len(result.scalars().all())
