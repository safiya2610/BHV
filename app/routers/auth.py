from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from db import get_db
from app.services.auth_service import *
from app.services.admin_service import is_admin

router = APIRouter(prefix="/api/auth")

@router.get("/login/google")
async def login_google(request: Request):
    return await google_login_redirect(request)

@router.get("/google/callback")
async def google_callback(request: Request, db=Depends(get_db)):
    user = await google_callback_handler(request, db)

    request.session["user"] = user["name"]
    request.session["email"] = user["email"]
    request.session["is_admin"] = is_admin(request, db)

    return RedirectResponse("/", status_code=303)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
