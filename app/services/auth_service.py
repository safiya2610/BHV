import logging
import sqlite3
from fastapi import Request

from config import GOOGLE_REDIRECT_URI
from auth_google import oauth

logger = logging.getLogger("bhv.auth")


async def google_login_redirect(request: Request):
    return await oauth.google.authorize_redirect(
        request,
        GOOGLE_REDIRECT_URI,
        state=None
    )


async def google_callback_handler(request: Request, db):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        logger.exception("Google authorize_access_token failed: %s", exc)
        return None

    try:
        resp = await oauth.google.get("https://www.googleapis.com/oauth2/v2/userinfo", token=token)
        userinfo = resp.json()
    except Exception as exc:
        logger.exception("Failed to fetch Google userinfo: %s", exc)
        return None

    if not userinfo or "email" not in userinfo:
        logger.error("Missing userinfo or email in Google response")
        return None

    if userinfo.get("email_verified") is False:
        logger.warning("Unverified Google email blocked")
        return None

    email = userinfo["email"].strip().lower()
    name = (userinfo.get("name") or email.split("@")[0]).strip()

    cur = db.cursor()

    try:
        cur.execute("SELECT email FROM users WHERE email=?", (email,))
        exists = cur.fetchone()

        if not exists:
            cur.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, None),
            )
            db.commit()

    except sqlite3.IntegrityError:
        db.rollback()

    except Exception as exc:
        db.rollback()
        logger.exception("Failed to upsert user during Google callback: %s", exc)
        return None

    return {
        "name": name,
        "email": email
    }
