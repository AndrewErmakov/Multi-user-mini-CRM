from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Activity
from .base import BaseRepository


class ActivityRepository(BaseRepository[Activity]):
    def __init__(self, db: AsyncSession):
        super().__init__(Activity, db)

    async def get_deal_activities(
        self, deal_id: int, organization_id: int, skip: int = 0, limit: int = 100
    ) -> list[Activity]:
        from app.models.deal import Deal

        query = (
            select(Activity)
            .join(Deal, Activity.deal_id == Deal.id)
            .where(and_(Activity.deal_id == deal_id, Deal.organization_id == organization_id))
            .order_by(Activity.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all() # type: ignore

    async def count_deal_activities(self, deal_id: int, organization_id: int) -> int:
        from app.models.deal import Deal

        query = (
            select(Activity)
            .join(Deal, Activity.deal_id == Deal.id)
            .where(and_(Activity.deal_id == deal_id, Deal.organization_id == organization_id))
        )

        result = await self.db.execute(query)
        return len(result.scalars().all())
