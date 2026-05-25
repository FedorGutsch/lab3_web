from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, RefreshToken
from ..schemas import UserCreate, UserLogin, UserOut, Token, RefreshRequest
from ..auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    save_refresh_token, verify_refresh_token, revoke_refresh_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where((User.username == data.username) | (User.email == data.email)))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким именем или email уже существует")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    await save_refresh_token(user.id, refresh, db)

    return Token(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=Token)
async def refresh_tokens(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    user = await verify_refresh_token(data.refresh_token, db)

    # Удаляем старый refresh-токен
    await revoke_refresh_token(user.id, db)

    # Создаём новую пару
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    await save_refresh_token(user.id, refresh, db)

    return Token(access_token=access, refresh_token=refresh)


@router.post("/logout")
async def logout(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await revoke_refresh_token(current.id, db)
    return {"detail": "Вы вышли из системы"}


@router.post("/logout-refresh")
async def logout_refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Выход по refresh-токену (без access-авторизации — нужен при автологауте по бездействию)."""
    try:
        user = await verify_refresh_token(data.refresh_token, db)
        await revoke_refresh_token(user.id, db)
    except HTTPException:
        # Токен уже недействителен — просто молча выходим
        pass
    return {"detail": "Вы вышли из системы"}
