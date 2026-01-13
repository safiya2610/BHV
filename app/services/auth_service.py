import logging
import sqlite3
from fastapi import Request

from config import GOOGLE_REDIRECT_URI
from auth_google import oauth

logger = logging.getLogger("bhv.auth")


async def google_login_redirect(request: Request):
    """
    Redirects user to Google OAuth consent screen
    """
    return await oauth.google.authorize_redirect(
        request,
        GOOGLE_REDIRECT_URI,
    )


async def google_callback_handler(request: Request, db):
    """
    Handles Google OAuth callback:
    - exchanges code for token
    - fetches user info
    - inserts user into DB if new
    - returns pure user data (NO redirect, NO session)
    """

    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        logger.exception("Google authorize_access_token failed: %s", exc)
        return None

    userinfo = token.get("userinfo")
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
        # Check if user already exists
        cur.execute("SELECT email FROM users WHERE email=?", (email,))
        exists = cur.fetchone()

        if not exists:
            # OAuth users have NULL password
            cur.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, None),
            )
            db.commit()

    except sqlite3.IntegrityError:
        # Race condition safety
        db.rollback()

    except Exception as exc:
        db.rollback()
        logger.exception("Failed to upsert user during Google callback: %s", exc)
        return None

    # ✅ RETURN PURE DATA ONLY
    return {
        "name": name,
        "email": email
    }
