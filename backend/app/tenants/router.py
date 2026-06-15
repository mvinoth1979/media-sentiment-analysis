from fastapi import APIRouter, Depends, Query
from app.auth.dependencies import get_current_user
from app.storage.postgres import get_db

router = APIRouter()


@router.get("/brands")
def search_brands(
    q: str = Query("", description="Brand name filter"),
    _user: dict = Depends(get_current_user),
):
    db = get_db()
    rows = db.table("brands").select("id, name, agency_id").execute().data
    if q:
        q_lower = q.lower()
        rows = [r for r in rows if q_lower in r["name"].lower()]
    return rows
