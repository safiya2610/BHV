from fastapi import APIRouter, Request, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3, json

from db import get_db
from app.services.image_service import save_image, delete_image

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def require_user(request: Request) -> str:
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    return user


@router.get("/gallery")
def gallery(
    request: Request,
    user: str = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db),
):
    cur = db.cursor()
    cur.execute(
        "SELECT filename, metadata, narrative FROM images WHERE user_name=?",
        (user,),
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
            "current_user": user,
        }
    )


@router.post("/upload")
def upload_image(
    user: str = Depends(require_user),
    image: UploadFile = File(...),
    visibility: str = Form("private"),
    db: sqlite3.Connection = Depends(get_db),
):
    save_image(db, user, image, visibility)
    return RedirectResponse("/gallery", 303)


@router.post("/delete/{filename}")
def delete_image_route(
    filename: str,
    user: str = Depends(require_user),
    db: sqlite3.Connection = Depends(get_db),
):
    delete_image(db, user, filename)
    return RedirectResponse("/gallery", 303)
