import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.pipeline.scheduler import start_scheduler
from app.auth.router import router as auth_router
from app.tenants.router import router as tenant_router
from app.dashboard.router import router as dashboard_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    asyncio.create_task(_queue_loop())
    yield


async def _queue_loop():
    from app.pipeline.worker import process_queue
    while True:
        await asyncio.to_thread(process_queue, max_items=50)
        await asyncio.sleep(60)


app = FastAPI(title="MediaSense API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,      prefix="/auth",      tags=["auth"])
app.include_router(tenant_router,    prefix="/tenants",   tags=["tenants"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])


@app.get("/health")
def health():
    return {"status": "ok"}
