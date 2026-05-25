import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .database import init_db
from .models import User, Post, Subscription, Reaction, RefreshToken  # noqa: F401 — нужно для create_all
from .routers import auth, users, posts, subscriptions, reactions
from fastapi.middleware.cors import CORSMiddleware

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Social Network API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статика для аватаров
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(posts.router, prefix="/api")
app.include_router(subscriptions.router, prefix="/api")
app.include_router(reactions.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
