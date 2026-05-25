import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database import get_db
from ..models import User, Subscription
from ..schemas import UserOut, UserUpdate
from ..auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/me", response_model=UserOut)
async def get_me(current: User = Depends(get_current_user)):
    return current


@router.put("/me", response_model=UserOut)
async def update_me(data: UserUpdate, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if data.email is not None:
        current.email = data.email
    if data.bio is not None:
        current.bio = data.bio
    if data.avatar_url is not None:
        current.avatar_url = data.avatar_url
    await db.commit()
    await db.refresh(current)
    return current


@router.post("/me/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Проверяем тип файла
    allowed = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Допустимы только изображения (JPEG, PNG, GIF, WebP)")

    # Читаем содержимое
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:  # 2 МБ
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 2 МБ)")

    # Генерируем уникальное имя
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{current.id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Удаляем старый аватар (если это локальный файл)
    if current.avatar_url and current.avatar_url.startswith("/uploads/"):
        old_path = os.path.join(os.path.dirname(__file__), "..", "..", current.avatar_url.lstrip("/"))
        if os.path.exists(old_path):
            os.remove(old_path)

    # Сохраняем файл
    with open(filepath, "wb") as f:
        f.write(contents)

    # Обновляем URL в БД
    current.avatar_url = f"/uploads/{filename}"
    await db.commit()
    await db.refresh(current)
    return current


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@router.get("/", response_model=list[UserOut])
async def search_users(q: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(User).order_by(User.id)
    if q:
        stmt = stmt.where(or_(User.username.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")))
    result = await db.execute(stmt.limit(50))
    return result.scalars().all()
