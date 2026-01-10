from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import logging
import sys
import os
from pathlib import Path

from config import SECRET_KEY
from db import init_db

from app.routers.auth import router as auth_router
from app.routers.gallery import router as gallery_router
from app.routers.pages import router as pages_router
from app.routers.narrative import router as narrative_router
from app.middleware.security import SecurityHeadersMiddleware, install_exception_handlers
from fastapi.middleware.cors import CORSMiddleware

# -------------------------
# Logging setup
# -------------------------
logger = logging.getLogger("bhv")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)

# -------------------------
# FastAPI app
# -------------------------
app = FastAPI(
    title="BHV Platform",
    version="0.1.0",
)

# Environment flags
DEBUG = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"}
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]

# -------------------------
# Initialize DB
# -------------------------
init_db()

# -------------------------
# Middleware
# -------------------------
# SessionMiddleware is REQUIRED for:
# - login.html
# - signup.html
# - server-rendered pages
# - Google OAuth redirect flow
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",           # CSRF protection for OAuth flows
    https_only=not DEBUG,       # Secure cookies in non-debug environments
    max_age=60 * 60 * 24 * 7,   # 7 days
)

# CORS
if ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

# Security headers (CSP, HSTS, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# Global exception handlers
install_exception_handlers(app)

# -------------------------
# Static files
# -------------------------
BASE_DIR = Path(__file__).resolve().parent
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

# -------------------------
# Routers
# -------------------------
# Pages (HTML / Jinja)
app.include_router(pages_router)

# Auth (Google login + JWT issue)
app.include_router(auth_router)

# Protected features
app.include_router(gallery_router)
app.include_router(narrative_router)

# -------------------------
# Lifecycle events
# -------------------------
@app.on_event("startup")
async def on_startup():
    logger.info("Starting BHV Platform application")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down BHV Platform application")

# -------------------------
# Local run
# -------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=DEBUG,
    )
