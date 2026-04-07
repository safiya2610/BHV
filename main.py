from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import logging
import sys
from contextlib import asynccontextmanager

from config import SECRET_KEY
from db import init_db

from app.routers.auth import router as auth_router
from app.routers.gallery import router as gallery_router
from app.routers.pages import router as pages_router
from app.routers.narrative import router as narrative_router
from app.routers.admin import router as admin_router
from app.routers.export import router as export_router



logger = logging.getLogger("bhv")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting BHV Platform application")
    yield
    logger.info("Shutting down BHV Platform application")


app = FastAPI(
    title="BHV Platform",
    version="0.1.0",
    docs_url="/api-docs",
    redoc_url="/api-redoc",
    lifespan=lifespan,
)

from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    return RedirectResponse(url="/login", status_code=302)

init_db()

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(gallery_router)
app.include_router(narrative_router)
app.include_router(admin_router)
app.include_router(export_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
