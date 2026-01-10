from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.jwt_service import decode_token

security = HTTPBearer(auto_error=False)

def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
):
    if not creds:
        raise HTTPException(401, "Missing token")

    payload = decode_token(creds.credentials)
    if not payload or payload["type"] != "access":
        raise HTTPException(401, "Invalid token")

    return payload["sub"]
