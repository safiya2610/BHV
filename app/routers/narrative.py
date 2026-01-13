from fastapi import APIRouter, Form, Depends, Request
from fastapi.responses import RedirectResponse
import sqlite3

from db import get_db
from app.services.admin_service import is_admin

router = APIRouter()

def get_current_user_email(request: Request, db: sqlite3.Connection = Depends(get_db)):
    email = request.session.get("email")
    if not email:
        return None
    if is_admin(request, db) and request.session.get("view_user"):
        email = request.session.get("view_user")
    return email

@router.post("/update-narrative")
def update_narrative(
    request: Request,
    filename: str = Form(...),
    narrative: str = Form(""),
    db: sqlite3.Connection = Depends(get_db)
):
    user_email = get_current_user_email(request, db)
    if not user_email:
        return RedirectResponse("/login", 303)

    cur = db.cursor()
    cur.execute(
        """
        UPDATE images
        SET narrative = ?
        WHERE filename = ? AND user_name = ?
        """,
        (narrative.strip(), filename, user_email)
    )
    db.commit()

    # Keep the view_user set for the gallery to show the correct images
    if is_admin(request, db):
        request.session["view_user"] = user_email

    return RedirectResponse("/gallery", 303)
