from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from app.services.auth_service import (
    google_login_redirect,
    google_callback_handler,
)
from db import get_db
from app.middleware.ratelimit import limiter_dependency

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Lightweight rate limits to protect auth endpoints
rl_login = limiter_dependency(10, 60)      # 10 requests per minute
rl_callback = limiter_dependency(20, 60)   # 20 requests per minute

@router.get("/login/google")
async def login_google(request: Request, _rl=Depends(rl_login)):
    return await google_login_redirect(request)

@router.get("/google/callback")
async def google_callback(request: Request, db=Depends(get_db), _rl=Depends(rl_callback)):
    return await google_callback_handler(request, db)

@router.get("/logout", include_in_schema=False)
def ui_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)