from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, auth
from database import get_db

ALLOWED_TYPES = {"like", "love", "wow", "sad", "angry"}

router = APIRouter(prefix="/api/reactions", tags=["reactions"])


@router.post("")
def add_reaction(
    body: schemas.ReactionCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    if body.type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Reaction type must be one of {ALLOWED_TYPES}")

    post = db.query(models.Post).filter(models.Post.id == body.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = db.query(models.Reaction).filter(
        models.Reaction.user_id == current_user.id,
        models.Reaction.post_id == body.post_id,
        models.Reaction.type == body.type,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Reaction already exists")

    reaction = models.Reaction(user_id=current_user.id, post_id=body.post_id, type=body.type)
    db.add(reaction)
    db.commit()
    return {"detail": "Reaction added"}


@router.delete("/{post_id}/{reaction_type}")
def remove_reaction(
    post_id: int,
    reaction_type: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    reaction = db.query(models.Reaction).filter(
        models.Reaction.user_id == current_user.id,
        models.Reaction.post_id == post_id,
        models.Reaction.type == reaction_type,
    ).first()
    if not reaction:
        raise HTTPException(status_code=404, detail="Reaction not found")

    db.delete(reaction)
    db.commit()
    return {"detail": "Reaction removed"}


@router.get("/{post_id}")
def get_reactions(post_id: int, db: Session = Depends(get_db)):
    reactions = db.query(models.Reaction).filter(models.Reaction.post_id == post_id).all()
    counts: dict[str, int] = {}
    for r in reactions:
        counts[r.type] = counts.get(r.type, 0) + 1
    return {"counts": counts, "total": len(reactions)}
