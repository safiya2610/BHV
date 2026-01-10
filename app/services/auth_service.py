from fastapi.responses import RedirectResponse
from auth_google import oauth
from config import GOOGLE_REDIRECT_URI
import logging
import sqlite3

logger = logging.getLogger("bhv.auth")


async def google_login_redirect(request):
    # Authlib manages anti-CSRF state via the session under the hood
    return await oauth.google.authorize_redirect(
        request,
        GOOGLE_REDIRECT_URI,
    )


async def google_callback_handler(request, db):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        logger.exception("Google authorize_access_token failed: %s", exc)
        return RedirectResponse("/login?error=oauth_exchange_failed", status_code=303)

    userinfo = token.get("userinfo")
    if not userinfo or "email" not in userinfo:
        return RedirectResponse("/login?error=missing_userinfo", status_code=303)

    # Optionally enforce email verification when available
    if userinfo.get("email_verified") is False:
        return RedirectResponse("/login?error=email_not_verified", status_code=303)

    email = userinfo["email"].strip().lower()
    name = (userinfo.get("name") or email.split("@")[0]).strip()

    cur = db.cursor()
    try:
        cur.execute("SELECT email FROM users WHERE email=?", (email,))
        if not cur.fetchone():
            # Insert NULL for password for OAuth users
            cur.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, None),
            )
            db.commit()
    except sqlite3.IntegrityError:
        # Race condition: user might have been created concurrently
        db.rollback()
    except Exception:
        db.rollback()
        logger.exception("Failed to upsert user during Google callback")
        return RedirectResponse("/login?error=server_error", status_code=303)

    # Mark session as authenticated by email principal
    request.session["user"] = email

    
    return RedirectResponse("/", status_code=303)
