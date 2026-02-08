import asyncio

from fastapi import FastAPI

from app.api import router as api_router
from app.config import settings
from app.logging_setup import setup_logging
from app.search import warm_cache
from app.bot import start_bot_task


setup_logging(settings.log_level)

app = FastAPI(title="CRM Access API")
app.include_router(api_router)


@app.on_event("startup")
async def on_startup() -> None:
    try:
        warm_cache()
    except Exception:
        pass
    loop = asyncio.get_event_loop()
    app.state.bot_task = start_bot_task(loop)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    task = getattr(app.state, "bot_task", None)
    if task:
        task.cancel()
