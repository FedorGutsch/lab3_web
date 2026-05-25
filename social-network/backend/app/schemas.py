from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ── Auth ──
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── User ──
class UserOut(BaseModel):
    id: int
    username: str
    email: str
    bio: str
    avatar_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


# ── Post ──
class PostCreate(BaseModel):
    title: str
    content: str = ""


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    author_username: str
    author_avatar: str = ""
    created_at: datetime
    updated_at: datetime
    reactions: list["ReactionOut"] = []

    model_config = {"from_attributes": True}


# ── Reaction ──
class ReactionCreate(BaseModel):
    emoji: str


class ReactionOut(BaseModel):
    id: int
    user_id: int
    post_id: int
    emoji: str

    model_config = {"from_attributes": True}


# ── Subscription ──
class SubscriptionOut(BaseModel):
    id: int
    follower_id: int
    following_id: int

    model_config = {"from_attributes": True}


PostOut.model_rebuild()
