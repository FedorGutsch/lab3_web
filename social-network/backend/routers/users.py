from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, auth
from database import get_db
from routers.auth import _user_out

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/search", response_model=list[schemas.UserOut])
def search_users(q: str = "", db: Session = Depends(get_db)):
    users = db.query(models.User).filter(
        (models.User.username.ilike(f"%{q}%")) | (models.User.email.ilike(f"%{q}%"))
    ).limit(20).all()
    return [_user_out(u) for u in users]


@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_out(user)


@router.put("/me", response_model=schemas.UserOut)
def update_me(
    body: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    if body.username:
        existing = db.query(models.User).filter(models.User.username == body.username, models.User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = body.username
    if body.email:
        existing = db.query(models.User).filter(models.User.email == body.email, models.User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        current_user.email = body.email
    if body.bio is not None:
        current_user.bio = body.bio
    if body.avatar_url is not None:
        current_user.avatar_url = body.avatar_url

    db.commit()
    db.refresh(current_user)
    return _user_out(current_user)
