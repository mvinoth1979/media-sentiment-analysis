from fastapi import APIRouter, Depends, Query
from app.auth.dependencies import get_current_user
from app.storage.postgres import get_db

router = APIRouter()


@router.get("/brands")
def search_brands(
    q: str = Query("", description="Brand name filter"),
    user: dict = Depends(get_current_user),
):
    db = get_db()
    roles = db.table("user_roles").select("agency_id, brand_id") \
              .eq("user_id", user["user_id"]).execute().data

    agency_ids = {r["agency_id"] for r in roles if r.get("agency_id")}
    brand_ids = {r["brand_id"] for r in roles if r.get("brand_id")}

    rows_by_id: dict[str, dict] = {}
    if agency_ids:
        for r in db.table("brands").select("id, name, agency_id") \
                    .in_("agency_id", list(agency_ids)).execute().data:
            rows_by_id[r["id"]] = r
    if brand_ids:
        for r in db.table("brands").select("id, name, agency_id") \
                    .in_("id", list(brand_ids)).execute().data:
            rows_by_id[r["id"]] = r

    rows = list(rows_by_id.values())
    if q:
        q_lower = q.lower()
        rows = [r for r in rows if q_lower in r["name"].lower()]
    return rows
