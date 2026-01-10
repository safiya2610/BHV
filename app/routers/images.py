from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/api")

@router.get("/images")
def images(user=Depends(get_current_user)):
    return {"message": "Protected", "user": user}
