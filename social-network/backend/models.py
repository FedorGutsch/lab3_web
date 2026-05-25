from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    bio = Column(Text, default="")
    avatar_url = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="author", lazy="selectin")
    subscriptions = relationship(
        "Subscription", foreign_keys="Subscription.subscriber_id", back_populates="subscriber", lazy="selectin"
    )
    subscribers = relationship(
        "Subscription", foreign_keys="Subscription.subscribed_to_id", back_populates="subscribed_to", lazy="selectin"
    )


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", back_populates="posts")
    reactions = relationship("Reaction", back_populates="post", lazy="selectin", cascade="all, delete-orphan")


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("subscriber_id", "subscribed_to_id", name="uq_subscription"),)

    id = Column(Integer, primary_key=True, index=True)
    subscriber_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscribed_to_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    subscriber = relationship("User", foreign_keys=[subscriber_id], back_populates="subscriptions")
    subscribed_to = relationship("User", foreign_keys=[subscribed_to_id], back_populates="subscribers")


class Reaction(Base):
    __tablename__ = "reactions"
    __table_args__ = (UniqueConstraint("user_id", "post_id", "type", name="uq_reaction"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    type = Column(String(30), nullable=False)  # like, love, wow, sad, angry
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    post = relationship("Post", back_populates="reactions")
