from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UserNotMemberOfOrganizationException
from app.database.session import get_db
from app.repositories import OrganizationMemberRepository, UserRepository

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = jwt.decode(
            credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
            )

        try:
            user_id = int(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID in token"
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
        )

    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_organization(
    x_organization_id: int = Header(..., alias="X-Organization-Id"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member_repo = OrganizationMemberRepository(db)
    membership = await member_repo.get_user_membership(current_user.id, x_organization_id)

    if not membership:
        raise UserNotMemberOfOrganizationException("User is not a member of this organization")

    return {
        "organization_id": x_organization_id,
        "user_role": membership.role,
        "membership": membership,
    }
