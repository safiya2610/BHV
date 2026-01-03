from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from db import get_db

router = APIRouter()

@router.post("/update-narrative")
async def update_narrative(
    filename: str = Form(...),
    narrative: str = Form("")
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE images SET narrative = ? WHERE filename = ?",
        (narrative.strip(), filename)
    )

    conn.commit()
    conn.close()

    return RedirectResponse(url="/gallery", status_code=303)
