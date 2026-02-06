from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
from db import get_db
import csv
import io
import json
from datetime import datetime
from typing import Dict, Any

router = APIRouter(prefix="/my-data")

def get_current_user(request: Request) -> str:
    """Get current user email from session."""
    user_email = request.session.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_email

def generate_user_csv(db, user_email: str) -> str:
    """Generate CSV data for user's images."""
    cur = db.cursor()
    cur.execute(
        """
        SELECT filename, metadata, narrative, visibility, upload_date, file_size
        FROM images
        WHERE user_name = ?
        ORDER BY upload_date DESC
        """,
        (user_email,)
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Description', 'Filename', 'File Size (KB)', 'Upload Date', 'Metadata'])

    for row in cur.fetchall():
        filename, metadata, narrative, visibility, upload_date, file_size = row

        title = "Untitled"
        description = ""
        meta_str = metadata or ""
        if metadata:
            try:
                meta_dict = json.loads(metadata)
                title = meta_dict.get('title', filename)
                description = meta_dict.get('description', narrative or "")
            except:
                title = filename
                description = narrative or ""

        try:
            dt = datetime.fromisoformat(upload_date)
            formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            formatted_date = upload_date or "Unknown"

        writer.writerow([title, description, filename, f"{file_size:.2f}" if file_size else "0.00", formatted_date, meta_str])

    return output.getvalue()

def generate_user_json(db, user_email: str) -> Dict[str, Any]:
    """Generate JSON data for user's complete data."""
    cur = db.cursor()

    
    cur.execute("SELECT name, email FROM users WHERE email = ?", (user_email,))
    user_row = cur.fetchone()
    if not user_row:
        user_name = "Unknown"
    else:
        user_name, user_email = user_row

    cur.execute(
        """
        SELECT filename, metadata, narrative, visibility, upload_date, file_size
        FROM images
        WHERE user_name = ?
        ORDER BY upload_date DESC
        """,
        (user_email,)
    )

    images = []
    total_storage = 0.0

    for row in cur.fetchall():
        filename, metadata, narrative, visibility, upload_date, file_size = row
        total_storage += file_size or 0

        meta_dict = {}
        if metadata:
            try:
                meta_dict = json.loads(metadata)
            except:
                pass

        images.append({
            "title": meta_dict.get('title', filename),
            "description": meta_dict.get('description', narrative or ""),
            "filename": filename,
            "file_size_kb": round(file_size or 0, 2),
            "uploaded_at": upload_date or "Unknown",
            "metadata": meta_dict
        })

    
    join_date = datetime.now().isoformat()
    if images:
        try:
            join_date = min(img['uploaded_at'] for img in images if img['uploaded_at'] != "Unknown")
        except:
            pass

    return {
        "user": {
            "username": user_name,
            "email": user_email,
            "member_since": join_date,
            "total_images": len(images),
            "total_storage_mb": round(total_storage / 1024, 2)
        },
        "images": images,
        "export_date": datetime.now().isoformat()
    }

@router.get("/csv")
async def export_my_data_csv(request: Request, db=Depends(get_db)):
    """Export current user's data as CSV."""
    user_email = get_current_user(request)

    csv_data = generate_user_csv(db, user_email)
    filename = f"bhv_my_data_{user_email.split('@')[0]}_{datetime.now().strftime('%Y%m%d')}.csv"

    def iter_csv():
        yield csv_data

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/json")
async def export_my_data_json(request: Request, db=Depends(get_db)):
    """Export current user's data as JSON."""
    user_email = get_current_user(request)

    json_data = generate_user_json(db, user_email)
    filename = f"bhv_my_data_{user_email.split('@')[0]}_{datetime.now().strftime('%Y%m%d')}.json"

    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)

    def iter_json():
        yield json_str

    return StreamingResponse(
        iter_json(),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
