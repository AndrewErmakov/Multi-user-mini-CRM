from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Contact
from .base import BaseRepository


class ContactRepository(BaseRepository[Contact]):
    def __init__(self, db: AsyncSession):
        super().__init__(Contact, db)

    async def get_organization_contacts(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        owner_id: int | None = None,
    ) -> list[Contact]:
        query = select(Contact).where(Contact.organization_id == organization_id)

        if search:
            query = query.where(
                (Contact.name.ilike(f"%{search}%")) | (Contact.email.ilike(f"%{search}%"))
            )

        if owner_id:
            query = query.where(Contact.owner_id == owner_id)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_organization_contacts(
        self, organization_id: int, search: str | None = None, owner_id: int | None = None
    ) -> int:
        query = select(Contact).where(Contact.organization_id == organization_id)

        if search:
            query = query.where(
                (Contact.name.ilike(f"%{search}%")) | (Contact.email.ilike(f"%{search}%"))
            )

        if owner_id:
            query = query.where(Contact.owner_id == owner_id)

        result = await self.db.execute(query)
        return len(result.scalars().all())

    async def get_contact_with_organization(
        self, contact_id: int, organization_id: int
    ) -> Contact | None:
        result = await self.db.execute(
            select(Contact).where(
                and_(Contact.id == contact_id, Contact.organization_id == organization_id)
            )
        )
        return result.scalar_one_or_none()
