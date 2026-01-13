from datetime import datetime, timedelta
from jose import jwt, JWTError
from config import *

def create_access_token(sub: str):
    payload = {
        "sub": sub,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(sub: str):
    payload = {
        "sub": sub,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_token(token: str, token_type: str = None):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if token_type and payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None
