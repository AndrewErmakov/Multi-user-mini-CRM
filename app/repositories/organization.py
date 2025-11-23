from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Organization, OrganizationMember
from .base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, db: AsyncSession):
        super().__init__(Organization, db)


class OrganizationMemberRepository(BaseRepository[OrganizationMember]):
    def __init__(self, db: AsyncSession):
        super().__init__(OrganizationMember, db)

    async def get_user_membership(
        self, user_id: int, organization_id: int
    ) -> OrganizationMember | None:
        result = await self.db.execute(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_user_organizations(self, user_id: int) -> list[Organization]:
        result = await self.db.execute(
            select(Organization)
            .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
            .where(OrganizationMember.user_id == user_id)
        )
        return result.scalars().all()
