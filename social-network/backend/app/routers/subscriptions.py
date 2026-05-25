from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, Subscription
from ..schemas import SubscriptionOut
from ..auth import get_current_user

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/{user_id}", response_model=SubscriptionOut)
async def subscribe(user_id: int, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="Нельзя подписаться на себя")
    result = await db.execute(select(User).where(User.id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    existing = await db.execute(
        select(Subscription).where(Subscription.follower_id == current.id, Subscription.following_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Вы уже подписаны")

    sub = Subscription(follower_id=current.id, following_id=user_id)
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.delete("/{user_id}")
async def unsubscribe(user_id: int, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subscription).where(Subscription.follower_id == current.id, Subscription.following_id == user_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Подписка не найдена")
    await db.delete(sub)
    await db.commit()
    return {"detail": "Отписка выполнена"}


@router.get("/followers", response_model=list[SubscriptionOut])
async def get_followers(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscription).where(Subscription.following_id == current.id))
    return result.scalars().all()


@router.get("/following", response_model=list[SubscriptionOut])
async def get_following(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscription).where(Subscription.follower_id == current.id))
    return result.scalars().all()


@router.get("/is_following/{user_id}")
async def is_following(user_id: int, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subscription).where(Subscription.follower_id == current.id, Subscription.following_id == user_id)
    )
    return {"is_following": result.scalar_one_or_none() is not None}
