import os
from dotenv import load_dotenv

load_dotenv()

IS_RENDER = os.getenv("RENDER") is not None

SECRET_KEY = os.getenv("SECRET_KEY", "test_secret_key")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost")

if IS_RENDER:
    if not SECRET_KEY:
        raise RuntimeError("Missing SECRET_KEY")

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
        raise RuntimeError("Missing Google OAuth env vars")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
JWT_ALGORITHM = "HS256"