from jose import jwt, JWTError
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import User, RefreshToken

SECRET_KEY = "super-secret-key-change-in-prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1
REFRESH_TOKEN_EXPIRE_HOURS = 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=REFRESH_TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": str(user_id), "exp": expire, "type": "refresh"}, SECRET_KEY, algorithm=ALGORITHM)


async def save_refresh_token(user_id: int, token: str, db: AsyncSession):
    """Сохраняем refresh-токен в БД."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    # Удаляем старые refresh-токены этого пользователя
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))

    rt = RefreshToken(token=token, user_id=user_id, expires_at=expires_at)
    db.add(rt)
    await db.commit()


async def verify_refresh_token(token: str, db: AsyncSession) -> User:
    """Проверяем refresh-токен: валидность JWT + наличие в БД + не истёк."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Неверный тип токена")
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Недействительный refresh-токен")

    # Ищем в БД
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == token, RefreshToken.user_id == user_id)
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise HTTPException(status_code=401, detail="Refresh-токен не найден")

    # Проверяем срок
    if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        await db.delete(stored)
        await db.commit()
        raise HTTPException(status_code=401, detail="Refresh-токен истёк")

    # Находим пользователя
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return user


async def revoke_refresh_token(user_id: int, db: AsyncSession):
    """Удаляем refresh-токен из БД (выход)."""
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
    await db.commit()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Если это refresh-токен, не пускаем как access
        if payload.get("type") == "refresh":
            raise credentials_exception
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
