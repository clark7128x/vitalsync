from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import auth, privacy, subscriptions, wearables
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="VitalSync API", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(subscriptions.router)
app.include_router(wearables.router)
app.include_router(privacy.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
