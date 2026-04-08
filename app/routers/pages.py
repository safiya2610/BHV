import sqlite3
import os
import re
import uuid
from collections import Counter
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from db import get_db
from app.services.admin_service import is_admin

router = APIRouter()
templates = Jinja2Templates(directory="templates")
DOCS_UPLOAD_DIR = os.path.join("static", "docs_uploads")
ALLOWED_DOC_EXTENSIONS = {".pdf", ".md", ".txt", ".doc", ".docx", ".png", ".jpg", ".jpeg"}
DEFAULT_DOCS = [
    {
        "slug": "overview-fuzzy-behavioral-vault",
        "title": "Overview",
        "section": "Documentation [v1.0.x]",
        "summary": "Understand the purpose of BHV and how fuzzy interpretation supports contextual visual records.",
        "content": (
            "BHV (Behavioral Health Vault) helps preserve image-based narratives for recovery journeys.\n\n"
            "The fuzzy approach maps uncertain emotional cues and social patterns from visual artifacts, "
            "so clinicians and support teams can interpret trends with richer context."
        ),
        "tags": "fuzzy, overview, behavior",
        "attachment_name": None,
        "created_at": None,
        "created_by": "system"
    },
    {
        "slug": "fuzzy-approach-concepts",
        "title": "Concepts",
        "section": "Documentation [v1.0.x]",
        "summary": "How fuzzy membership, linguistic variables, and narrative signals connect in BHV.",
        "content": (
            "Core fuzzy concepts in BHV:\n"
            "1. Membership scoring for emotional ambiguity.\n"
            "2. Rule-based interpretation across multiple visual indicators.\n"
            "3. Narrative + image fusion for contextual understanding."
        ),
        "tags": "fuzzy, concepts, emotion",
        "attachment_name": None,
        "created_at": None,
        "created_by": "system"
    },
    {
        "slug": "quickstart-doc-workflow",
        "title": "Quickstart",
        "section": "Documentation [v1.0.x]",
        "summary": "A practical workflow to upload images, attach narratives, and review metadata.",
        "content": (
            "Quickstart:\n"
            "- Upload artwork or photos in Gallery.\n"
            "- Add narrative context.\n"
            "- Review fuzzy metadata output.\n"
            "- Use Docs to publish references and methodology updates."
        ),
        "tags": "quickstart, workflow, gallery",
        "attachment_name": None,
        "created_at": None,
        "created_by": "system"
    }
]


def _slugify(value: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return base or f"doc-{uuid.uuid4().hex[:8]}"


def _ensure_unique_slug(db: sqlite3.Connection, base_slug: str) -> str:
    cur = db.cursor()
    slug = base_slug
    suffix = 1
    while True:
        cur.execute("SELECT 1 FROM docs_entries WHERE slug = ?", (slug,))
        if not cur.fetchone():
            return slug
        suffix += 1
        slug = f"{base_slug}-{suffix}"


def _docs_table_exists(db: sqlite3.Connection):
    cur = db.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS docs_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            section TEXT NOT NULL DEFAULT 'General',
            summary TEXT,
            content TEXT NOT NULL,
            tags TEXT,
            attachment_name TEXT,
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_published INTEGER DEFAULT 1
        )
        """
    )
    db.commit()

@router.get("/")
def home(request: Request):
    if not request.session.get("user"):
        return RedirectResponse("/login", 303)

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"request": request, "user": request.session["user"]}
    )

@router.get("/login")
def login_page(request: Request):
    error_code = request.query_params.get("error")
    error_map = {
        "google_auth_failed": "Google sign-in failed. Please try again.",
    }
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "error": error_map.get(error_code)
        }
    )

@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: sqlite3.Connection = Depends(get_db)
):
    normalized_email = email.strip().lower()

    cur = db.cursor()
    cur.execute(
        "SELECT name, email, password FROM users WHERE email = ?",
        (normalized_email,)
    )
    user_row = cur.fetchone()

    if not user_row or not user_row["password"] or user_row["password"] != password:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "error": "Invalid email or password.",
                "prefill_email": normalized_email
            },
            status_code=400
        )

    request.session["user"] = user_row["name"] or user_row["email"].split("@")[0]
    request.session["email"] = user_row["email"]
    request.session["is_admin"] = is_admin(request, db)

    return RedirectResponse("/", status_code=303)

@router.get("/signup")
def signup_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="signup.html",
        context={"request": request}
    )

@router.post("/signup")
def signup_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: sqlite3.Connection = Depends(get_db)
):
    normalized_name = name.strip()
    normalized_email = email.strip().lower()

    cur = db.cursor()
    cur.execute("SELECT 1 FROM users WHERE email = ?", (normalized_email,))
    if cur.fetchone():
        return templates.TemplateResponse(
            request=request,
            name="signup.html",
            context={
                "request": request,
                "error": "An account with this email already exists.",
                "prefill_name": normalized_name,
                "prefill_email": normalized_email
            },
            status_code=400
        )

    cur.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (normalized_name, normalized_email, password)
    )
    db.commit()

    request.session["user"] = normalized_name or normalized_email.split("@")[0]
    request.session["email"] = normalized_email
    request.session["is_admin"] = is_admin(request, db)

    return RedirectResponse("/", status_code=303)


@router.get("/docs")
def docs_page(request: Request, db: sqlite3.Connection = Depends(get_db)):
    if not request.session.get("user"):
        return RedirectResponse("/login", status_code=303)

    _docs_table_exists(db)
    selected_slug = (request.query_params.get("doc") or "").strip().lower()
    query = (request.query_params.get("q") or "").strip().lower()

    cur = db.cursor()
    cur.execute(
        """
        SELECT slug, title, section, summary, content, tags, attachment_name, created_at, created_by
        FROM docs_entries
        WHERE is_published = 1
        ORDER BY section COLLATE NOCASE, title COLLATE NOCASE
        """
    )
    rows = cur.fetchall()
    docs_entries = [dict(r) for r in rows]
    if not docs_entries:
        docs_entries = DEFAULT_DOCS

    if query:
        docs_entries = [
            d for d in docs_entries
            if query in (d.get("title") or "").lower()
            or query in (d.get("summary") or "").lower()
            or query in (d.get("content") or "").lower()
            or query in (d.get("section") or "").lower()
            or query in (d.get("tags") or "").lower()
        ]

    selected_doc = None
    if selected_slug:
        selected_doc = next((d for d in docs_entries if d.get("slug") == selected_slug), None)

    section_counter = Counter((d.get("section") or "General") for d in docs_entries)
    tag_counter = Counter()
    for d in docs_entries:
        raw_tags = d.get("tags") or ""
        for tag in [t.strip() for t in raw_tags.split(",") if t.strip()]:
            tag_counter[tag] += 1

    return templates.TemplateResponse(
        request=request,
        name="docs.html",
        context={
            "request": request,
            "user": request.session.get("user"),
            "docs_entries": docs_entries,
            "selected_doc": selected_doc,
            "selected_slug": selected_slug,
            "search_query": query,
            "section_counts": sorted(section_counter.items(), key=lambda x: x[0].lower()),
            "tag_counts": sorted(tag_counter.items(), key=lambda x: x[0].lower()),
            "is_admin": bool(request.session.get("is_admin")),
            "upload_error": request.query_params.get("error")
        }
    )


@router.post("/docs/upload")
async def docs_upload(
    request: Request,
    title: str = Form(...),
    section: str = Form("Documentation [v1.0.x]"),
    summary: str = Form(""),
    content: str = Form(...),
    tags: str = Form(""),
    attachment: UploadFile | None = File(None),
    db: sqlite3.Connection = Depends(get_db)
):
    if not request.session.get("user"):
        return RedirectResponse("/login", status_code=303)

    if not request.session.get("is_admin"):
        return RedirectResponse("/docs?error=admin_only", status_code=303)

    clean_title = title.strip()
    clean_content = content.strip()
    clean_section = section.strip() or "Documentation [v1.0.x]"
    clean_summary = summary.strip()
    clean_tags = tags.strip()

    if not clean_title or not clean_content:
        return RedirectResponse("/docs?error=missing_required_fields", status_code=303)

    _docs_table_exists(db)
    base_slug = _slugify(clean_title)
    slug = _ensure_unique_slug(db, base_slug)

    attachment_name = None
    if attachment and attachment.filename:
        ext = os.path.splitext(attachment.filename)[1].lower()
        if ext not in ALLOWED_DOC_EXTENSIONS:
            return RedirectResponse("/docs?error=invalid_attachment_type", status_code=303)

        os.makedirs(DOCS_UPLOAD_DIR, exist_ok=True)
        attachment_name = f"{uuid.uuid4().hex}{ext}"
        target_path = os.path.join(DOCS_UPLOAD_DIR, attachment_name)
        with open(target_path, "wb") as f:
            f.write(await attachment.read())

    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO docs_entries (slug, title, section, summary, content, tags, attachment_name, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            slug,
            clean_title,
            clean_section,
            clean_summary,
            clean_content,
            clean_tags,
            attachment_name,
            request.session.get("email")
        )
    )
    db.commit()

    return RedirectResponse(f"/docs?doc={slug}", status_code=303)


@router.get("/research")
def research_redirect():
    return RedirectResponse("/docs", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
