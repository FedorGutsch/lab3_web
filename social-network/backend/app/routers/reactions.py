from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, Post, Reaction
from ..schemas import ReactionCreate, ReactionOut
from ..auth import get_current_user

router = APIRouter(prefix="/reactions", tags=["reactions"])


@router.post("/{post_id}", response_model=ReactionOut)
async def add_reaction(post_id: int, data: ReactionCreate, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Пост не найден")

    existing = await db.execute(
        select(Reaction).where(Reaction.user_id == current.id, Reaction.post_id == post_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Вы уже оставили реакцию на этот пост")

    reaction = Reaction(user_id=current.id, post_id=post_id, emoji=data.emoji)
    db.add(reaction)
    await db.commit()
    await db.refresh(reaction)
    return reaction


@router.post("/{post_id}/toggle")
async def toggle_reaction(post_id: int, data: ReactionCreate, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Логика toggle:
    - Если реакции нет → создаём
    - Если реакция с таким же эмодзи → удаляем
    - Если реакция с другим эмодзи → меняем на новый
    """
    result = await db.execute(select(Post).where(Post.id == post_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Пост не найден")

    existing = await db.execute(
        select(Reaction).where(Reaction.user_id == current.id, Reaction.post_id == post_id)
    )
    reaction = existing.scalar_one_or_none()

    if not reaction:
        # Нет реакции → создаём
        reaction = Reaction(user_id=current.id, post_id=post_id, emoji=data.emoji)
        db.add(reaction)
        await db.commit()
        await db.refresh(reaction)
        return {"action": "created", "reaction": {"id": reaction.id, "emoji": reaction.emoji, "user_id": reaction.user_id, "post_id": reaction.post_id}}

    if reaction.emoji == data.emoji:
        # Тот же эмодзи → удаляем
        await db.delete(reaction)
        await db.commit()
        return {"action": "removed"}

    # Другой эмодзи → меняем
    reaction.emoji = data.emoji
    await db.commit()
    await db.refresh(reaction)
    return {"action": "changed", "reaction": {"id": reaction.id, "emoji": reaction.emoji, "user_id": reaction.user_id, "post_id": reaction.post_id}}


@router.delete("/{post_id}")
async def remove_reaction(post_id: int, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Reaction).where(Reaction.user_id == current.id, Reaction.post_id == post_id)
    )
    reaction = result.scalar_one_or_none()
    if not reaction:
        raise HTTPException(status_code=404, detail="Реакция не найдена")
    await db.delete(reaction)
    await db.commit()
    return {"detail": "Реакция удалена"}


@router.get("/{post_id}", response_model=list[ReactionOut])
async def get_reactions(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Reaction).where(Reaction.post_id == post_id))
    return result.scalars().all()
