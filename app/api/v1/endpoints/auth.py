from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.repositories import UserRepository
from app.schemas import Token, UserLogin, UserRegister
from app.services import UserService
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    auth_service = AuthService(db)

    user_repo = UserRepository(db)
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = await user_service.create_user_with_organization(
        user_data.email, user_data.password, user_data.name, user_data.organization_name
    )

    access_token = auth_service.create_access_token(data={"sub": str(user.id)})
    refresh_token = auth_service.create_access_token(
        data={"sub": str(user.id)}, expires_delta=timedelta(days=7)
    )

    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token)


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(user_data.email, user_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or/and password"
        )

    access_token = auth_service.create_access_token(data={"sub": str(user.id)})
    refresh_token = auth_service.create_access_token(
        data={"sub": str(user.id)}, expires_delta=timedelta(days=7)
    )

    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token)
