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


def generate_admin_users_csv(db) -> str:
    """Generate CSV of all users for admin."""
    cur = db.cursor()
    cur.execute(
        """
        SELECT u.name, u.email, CASE WHEN a.email IS NOT NULL THEN 'Yes' ELSE 'No' END as is_admin,
               COUNT(i.id) as total_images, COALESCE(SUM(i.file_size), 0) / 1024 as storage_mb,
               MIN(i.upload_date) as join_date
        FROM users u
        LEFT JOIN admins a ON u.email = a.email
        LEFT JOIN images i ON u.email = i.user_name
        GROUP BY u.id, u.name, u.email, a.email
        ORDER BY u.name
        """
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Username', 'Email', 'Admin Status', 'Total Images', 'Storage (MB)', 'Join Date'])

    for row in cur.fetchall():
        name, email, is_admin, total_images, storage_mb, join_date = row
        # Format join date
        try:
            if join_date:
                dt = datetime.fromisoformat(join_date)
                formatted_join = dt.strftime('%Y-%m-%d')
            else:
                formatted_join = "N/A"
        except:
            formatted_join = join_date or "N/A"

        writer.writerow([name or "N/A", email, is_admin, total_images, f"{storage_mb:.2f}", formatted_join])

    return output.getvalue()


def generate_admin_images_csv(db) -> str:
    """Generate CSV of all images for admin."""
    cur = db.cursor()
    cur.execute(
        """
        SELECT i.filename, i.user_name, i.narrative, i.visibility, i.upload_date, i.file_size,
               i.metadata
        FROM images i
        ORDER BY i.upload_date DESC
        """
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Owner', 'Filename', 'File Size (KB)', 'Upload Date', 'Visibility', 'Narrative'])

    for row in cur.fetchall():
        filename, user_name, narrative, visibility, upload_date, file_size, metadata = row

        # Parse metadata for title
        title = filename
        if metadata:
            try:
                meta_dict = json.loads(metadata)
                title = meta_dict.get('title', filename)
            except:
                pass

        # Format date
        try:
            dt = datetime.fromisoformat(upload_date)
            formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            formatted_date = upload_date or "Unknown"

        writer.writerow([
            title,
            user_name,
            filename,
            f"{file_size:.2f}" if file_size else "0.00",
            formatted_date,
            visibility,
            narrative or ""
        ])

    return output.getvalue()


@router.get("/admin/export/users")
def admin_export_users(request: Request, db=Depends(get_db)):
    """Export all users data as CSV (admin only)."""
    if not request.session.get("is_admin"):
        return RedirectResponse("/", status_code=303)

    csv_data = generate_admin_users_csv(db)
    filename = f"bhv_users_export_{datetime.now().strftime('%Y%m%d')}.csv"

    def iter_csv():
        yield csv_data

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/admin/export/images")
def admin_export_images(request: Request, db=Depends(get_db)):
    """Export all images data as CSV (admin only)."""
    if not request.session.get("is_admin"):
        return RedirectResponse("/", status_code=303)

    csv_data = generate_admin_images_csv(db)
    filename = f"bhv_images_export_{datetime.now().strftime('%Y%m%d')}.csv"

    def iter_csv():
        yield csv_data

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )









