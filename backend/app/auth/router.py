from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/verify")
async def verify_token(user: dict = Depends(get_current_user)):
    return {"user_id": user["user_id"], "email": user["email"]}
