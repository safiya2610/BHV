from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import json
import os
import uuid

from db import get_db
from app.services.image_service import save_image, delete_image
from app.services.admin_service import is_admin
from fuzzy_emotion import detect_fuzzy_emotion

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"


def require_user(request: Request, db: sqlite3.Connection = Depends(get_db)) -> str:
    email = request.session.get("email")
    if not email:
        return RedirectResponse("/login", 303)
    if is_admin(request, db) and request.session.get("view_user"):
        email = request.session.get("view_user")
    return email


@router.get("/gallery")
def gallery(
    request: Request,
    user: str = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cur = db.cursor()
    cur.execute(
        "SELECT filename, metadata, narrative FROM images WHERE user_name=?",
        (user,)
    )

    images = [
        (fn, json.loads(meta) if meta else {}, narrative)
        for fn, meta, narrative in cur.fetchall()
    ]

    return templates.TemplateResponse(
        "gallery.html",
        {
            "request": request,
            "images": images,
            "profile_user": user,
            "current_user": user
        }
    )


@router.post("/upload")
async def upload_image(
    request: Request,
    image: UploadFile = File(...),
    visibility: str = Form("private"),
    db=Depends(get_db)
):
    user_email = request.session.get("email")
    if not user_email:
        return RedirectResponse("/login", 303)

    ext = os.path.splitext(image.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(await image.read())

    metadata = detect_fuzzy_emotion(filepath)

    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO images (user_name, filename, metadata, visibility)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_email,  
            filename,
            json.dumps(metadata),
            visibility
        )
    )
    db.commit()

    return RedirectResponse("/gallery", 303)



@router.post("/delete/{filename}")
def delete_image_route(
    request: Request,
    filename: str,
    user: str = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db)
):
    delete_image(db, user, filename)

    
    if is_admin(request, db):
        request.session["view_user"] = user

    return RedirectResponse("/gallery", 303)
