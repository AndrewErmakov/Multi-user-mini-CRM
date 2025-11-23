from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import OrganizationMemberRepository, OrganizationRepository


class OrganizationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.org_repo = OrganizationRepository(db)
        self.member_repo = OrganizationMemberRepository(db)

    async def get_user_organizations(self, user_id: int) -> list:
        organizations = await self.member_repo.get_user_organizations(user_id)

        result = []
        for organization in organizations:
            membership = await self.member_repo.get_user_membership(user_id, organization.id)
            result.append(
                {
                    "id": organization.id,
                    "name": organization.name,
                    "created_at": organization.created_at,
                    "role": membership.role,
                }
            )

        return result
