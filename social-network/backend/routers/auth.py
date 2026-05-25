from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.TokenOut)
def register(body: schemas.RegisterIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(models.User).filter(models.User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = models.User(
        username=body.username,
        email=body.email,
        hashed_password=auth.hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.create_access_token(user.id)
    return schemas.TokenOut(access_token=token)


@router.post("/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not auth.verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token(user.id)
    return schemas.TokenOut(access_token=token)


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(auth.get_current_user)):
    return _user_out(current_user)


def _user_out(user: models.User) -> schemas.UserOut:
    return schemas.UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        bio=user.bio or "",
        avatar_url=user.avatar_url or "",
        created_at=user.created_at,
        subscribers_count=len(user.subscribers),
        subscriptions_count=len(user.subscriptions),
    )
