from datetime import datetime, timedelta

from jose import jwt

from app.core.config import settings


def create_test_token(user_id: int) -> str:
    """Создает тестовый JWT токен"""
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta

    # В соответствии с JWT стандартом, subject должен быть строкой
    to_encode = {"exp": expire, "sub": str(user_id)}

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
