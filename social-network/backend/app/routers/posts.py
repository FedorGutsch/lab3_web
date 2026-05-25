from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, Post, Subscription
from ..schemas import PostCreate, PostUpdate, PostOut
from ..auth import get_current_user

router = APIRouter(prefix="/posts", tags=["posts"])


async def _post_to_out(post: Post, db: AsyncSession) -> PostOut:
    result = await db.execute(select(User).where(User.id == post.author_id))
    author = result.scalar_one()
    from ..models import Reaction
    r = await db.execute(select(Reaction).where(Reaction.post_id == post.id))
    reactions = r.scalars().all()
    return PostOut(
        id=post.id,
        title=post.title,
        content=post.content,
        author_id=post.author_id,
        author_username=author.username,
        author_avatar=author.avatar_url or "",
        created_at=post.created_at,
        updated_at=post.updated_at,
        reactions=reactions,
    )


@router.post("/", response_model=PostOut)
async def create_post(data: PostCreate, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    post = Post(title=data.title, content=data.content, author_id=current.id)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return await _post_to_out(post, db)


@router.put("/{post_id}", response_model=PostOut)
async def update_post(post_id: int, data: PostUpdate, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    if post.author_id != current.id:
        raise HTTPException(status_code=403, detail="Нельзя редактировать чужой пост")
    if data.title is not None:
        post.title = data.title
    if data.content is not None:
        post.content = data.content
    await db.commit()
    await db.refresh(post)
    return await _post_to_out(post, db)


@router.delete("/{post_id}")
async def delete_post(post_id: int, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    if post.author_id != current.id:
        raise HTTPException(status_code=403, detail="Нельзя удалить чужой пост")
    await db.delete(post)
    await db.commit()
    return {"detail": "Удалено"}


@router.get("/feed", response_model=list[PostOut])
async def global_feed(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).order_by(Post.created_at.desc()).offset(skip).limit(limit))
    posts = result.scalars().all()
    return [await _post_to_out(p, db) for p in posts]


@router.get("/my", response_model=list[PostOut])
async def my_posts(skip: int = 0, limit: int = 20, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post).where(Post.author_id == current.id).order_by(Post.created_at.desc()).offset(skip).limit(limit)
    )
    posts = result.scalars().all()
    return [await _post_to_out(p, db) for p in posts]


@router.get("/following", response_model=list[PostOut])
async def following_posts(skip: int = 0, limit: int = 20, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub_ids = select(Subscription.following_id).where(Subscription.follower_id == current.id)
    result = await db.execute(
        select(Post).where(Post.author_id.in_(sub_ids)).order_by(Post.created_at.desc()).offset(skip).limit(limit)
    )
    posts = result.scalars().all()
    return [await _post_to_out(p, db) for p in posts]


@router.get("/user/{user_id}", response_model=list[PostOut])
async def user_posts(user_id: int, skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post).where(Post.author_id == user_id).order_by(Post.created_at.desc()).offset(skip).limit(limit)
    )
    posts = result.scalars().all()
    return [await _post_to_out(p, db) for p in posts]
