from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from db import get_db
import json

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/admin")
def admin_dashboard(request: Request, db=Depends(get_db)):
    if not request.session.get("is_admin"):
        return RedirectResponse("/", status_code=303)

    request.session.pop("view_user", None)

    cur = db.cursor()
    cur.execute("SELECT id, name, email FROM users")
    rows = cur.fetchall()

    users = [{"id": r[0], "name": r[1], "email": r[2]} for r in rows]

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "users": users
        }
    )


@router.get("/admin/user/{user_id}")
def admin_user_gallery(user_id: int, request: Request, db=Depends(get_db)):
    if not request.session.get("is_admin"):
        return RedirectResponse("/", 303)

    cur = db.cursor()
    cur.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    user_row = cur.fetchone()
    if not user_row:
        return RedirectResponse("/admin", status_code=303)

    email = user_row[0]

    cur.execute(
        """
        SELECT filename, metadata, narrative, visibility
        FROM images
        WHERE user_name = ?
        ORDER BY id DESC
        """,
        (email,)
    )

    images = []
    for r in cur.fetchall():
        meta = json.loads(r[1]) if r[1] else None
        images.append((r[0], meta, r[2], r[3]))

    return templates.TemplateResponse(
        "admin_user_gallery.html",
        {
            "request": request,
            "images": images,
            "profile_user": email
        }
    )

@router.post("/admin/delete-image")
def admin_delete_image(
    request: Request,
    filename: str = Form(...),
    user_email: str = Form(...),
    db=Depends(get_db)
):
    if not request.session.get("is_admin"):
        return RedirectResponse("/", status_code=303)

    cur = db.cursor()
    cur.execute(
        "DELETE FROM images WHERE filename=? AND user_name=?",
        (filename, user_email)
    )
    db.commit()

    return RedirectResponse(f"/admin/user/{user_email}", status_code=303)


@router.get("/admin/view-gallery/{email}")
def admin_view_gallery(email: str, request: Request, db=Depends(get_db)):
    if not request.session.get("is_admin"):
        return RedirectResponse("/", status_code=303)

    request.session["view_user"] = email
    return RedirectResponse("/gallery", status_code=303)


@router.post("/admin/update-narrative")
def admin_update_narrative(
    request: Request,
    filename: str = Form(...),
    narrative: str = Form(...),
    user_email: str = Form(...),
    db=Depends(get_db)
):
    if not request.session.get("is_admin"):
        return RedirectResponse("/", status_code=303)

    cur = db.cursor()
    cur.execute(
        """
        UPDATE images
        SET narrative=?
        WHERE filename=? AND user_name=?
        """,
        (narrative, filename, user_email)
    )
    db.commit()

    cur.execute("SELECT id FROM users WHERE email = ?", (user_email,))
    user_row = cur.fetchone()
    user_id = user_row[0] if user_row else 1  

    return RedirectResponse(f"/admin/user/{user_id}", status_code=303)









