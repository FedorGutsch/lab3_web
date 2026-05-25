from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


# ── Auth ──────────────────────────────────────────
class RegisterIn(BaseModel):
    username: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User ──────────────────────────────────────────
class UserOut(BaseModel):
    id: int
    username: str
    email: str
    bio: str = ""
    avatar_url: str = ""
    created_at: datetime
    subscribers_count: int = 0
    subscriptions_count: int = 0

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


# ── Post ──────────────────────────────────────────
class PostCreate(BaseModel):
    title: str
    content: str = ""


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class ReactionOut(BaseModel):
    id: int
    user_id: int
    type: str
    model_config = {"from_attributes": True}


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    author_username: str = ""
    created_at: datetime
    updated_at: datetime
    reactions: list[ReactionOut] = []

    model_config = {"from_attributes": True}


# ── Reaction ──────────────────────────────────────
class ReactionCreate(BaseModel):
    post_id: int
    type: str  # like, love, wow, sad, angry


# ── Subscription ──────────────────────────────────
class SubscriptionOut(BaseModel):
    id: int
    subscriber_id: int
    subscribed_to_id: int
    created_at: datetime
    model_config = {"from_attributes": True}
