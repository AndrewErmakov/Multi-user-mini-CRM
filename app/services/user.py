from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.repositories import OrganizationMemberRepository, OrganizationRepository, UserRepository


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.org_repo = OrganizationRepository(db)
        self.member_repo = OrganizationMemberRepository(db)

    async def create_user_with_organization(
        self, email: str, password: str, name: str, organization_name: str
    ):
        user = await self.user_repo.create(
            {"email": email, "hashed_password": get_password_hash(password), "name": name}
        )

        organization = await self.org_repo.create({"name": organization_name})

        await self.member_repo.create(
            {"organization_id": organization.id, "user_id": user.id, "role": "owner"}
        )

        return user
