from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.post("", response_model=schemas.PostOut)
def create_post(body: schemas.PostCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    post = models.Post(title=body.title, content=body.content, author_id=current_user.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return _post_out(post)


@router.get("", response_model=list[schemas.PostOut])
def get_posts(
    feed: str = Query("all", enum=["all", "mine", "subscriptions"]),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Post)

    if feed == "mine":
        query = query.filter(models.Post.author_id == current_user.id)
    elif feed == "subscriptions":
        sub_ids = [s.subscribed_to_id for s in current_user.subscriptions]
        if not sub_ids:
            return []
        query = query.filter(models.Post.author_id.in_(sub_ids))

    posts = query.order_by(models.Post.created_at.desc()).limit(50).all()
    return [_post_out(p) for p in posts]


@router.get("/{post_id}", response_model=schemas.PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return _post_out(post)


@router.put("/{post_id}", response_model=schemas.PostOut)
def update_post(
    post_id: int,
    body: schemas.PostUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your post")

    if body.title is not None:
        post.title = body.title
    if body.content is not None:
        post.content = body.content

    db.commit()
    db.refresh(post)
    return _post_out(post)


@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your post")

    db.delete(post)
    db.commit()
    return {"detail": "Post deleted"}


def _post_out(post: models.Post) -> schemas.PostOut:
    return schemas.PostOut(
        id=post.id,
        title=post.title,
        content=post.content,
        author_id=post.author_id,
        author_username=post.author.username if post.author else "",
        created_at=post.created_at,
        updated_at=post.updated_at,
        reactions=[
            schemas.ReactionOut(id=r.id, user_id=r.user_id, type=r.type)
            for r in (post.reactions or [])
        ],
    )
