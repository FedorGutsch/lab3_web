from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.get("", response_model=list[schemas.UserOut])
def my_subscriptions(current_user: models.User = Depends(auth.get_current_user)):
    from routers.auth import _user_out
    return [_user_out(s.subscribed_to) for s in current_user.subscriptions]


@router.post("/{user_id}")
def subscribe(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot subscribe to yourself")

    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(models.Subscription).filter(
        models.Subscription.subscriber_id == current_user.id,
        models.Subscription.subscribed_to_id == user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already subscribed")

    sub = models.Subscription(subscriber_id=current_user.id, subscribed_to_id=user_id)
    db.add(sub)
    db.commit()
    return {"detail": "Subscribed"}


@router.delete("/{user_id}")
def unsubscribe(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    sub = db.query(models.Subscription).filter(
        models.Subscription.subscriber_id == current_user.id,
        models.Subscription.subscribed_to_id == user_id,
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.delete(sub)
    db.commit()
    return {"detail": "Unsubscribed"}


@router.get("/check/{user_id}")
def check_subscription(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    exists = db.query(models.Subscription).filter(
        models.Subscription.subscriber_id == current_user.id,
        models.Subscription.subscribed_to_id == user_id,
    ).first()
    return {"subscribed": bool(exists)}
