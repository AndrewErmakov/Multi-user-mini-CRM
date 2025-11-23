from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Deal
from .base import BaseRepository


class DealRepository(BaseRepository[Deal]):
    def __init__(self, db: AsyncSession):
        super().__init__(Deal, db)

    async def get_organization_deals(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
        status: list[str] | None = None,
        stage: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        owner_id: int | None = None,
        order_by: str = "created_at",
        order: str = "desc",
    ) -> list[Deal]:
        query = select(Deal).where(Deal.organization_id == organization_id)

        if status:
            query = query.where(Deal.status.in_(status))

        if stage:
            query = query.where(Deal.stage == stage)

        if min_amount is not None:
            query = query.where(Deal.amount >= min_amount)

        if max_amount is not None:
            query = query.where(Deal.amount <= max_amount)

        if owner_id:
            query = query.where(Deal.owner_id == owner_id)

        if order_by == "amount":
            if order == "asc":
                query = query.order_by(Deal.amount.asc())
            else:
                query = query.order_by(Deal.amount.desc())
        else:
            if order == "asc":
                query = query.order_by(Deal.created_at.asc())
            else:
                query = query.order_by(Deal.created_at.desc())

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_organization_deals(
        self,
        organization_id: int,
        status: list[str] | None = None,
        stage: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        owner_id: int | None = None,
    ) -> int:
        query = select(Deal).where(Deal.organization_id == organization_id)

        if status:
            query = query.where(Deal.status.in_(status))

        if stage:
            query = query.where(Deal.stage == stage)

        if min_amount is not None:
            query = query.where(Deal.amount >= min_amount)

        if max_amount is not None:
            query = query.where(Deal.amount <= max_amount)

        if owner_id:
            query = query.where(Deal.owner_id == owner_id)

        result = await self.db.execute(query)
        return len(result.scalars().all())

    async def get_deal_with_organization(self, deal_id: int, organization_id: int) -> Deal | None:
        result = await self.db.execute(
            select(Deal).where(and_(Deal.id == deal_id, Deal.organization_id == organization_id))
        )
        return result.scalar_one_or_none()
