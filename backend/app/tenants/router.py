from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from app.auth.dependencies import get_current_user, require_role
from app.storage.postgres import get_db

router = APIRouter()


class BrandConfigUpdate(BaseModel):
    keywords: list[str] | None = None
    languages: list[str] | None = None
    states: list[str] | None = None
    competitors: list[str] | None = None
    portal_ids: list[str] | None = None


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


@router.put("/brands/{brand_id}/config")
def update_brand_config(
    brand_id: str,
    payload: BrandConfigUpdate,
    user: dict = Depends(require_role("agency_admin", "brand_admin")),
):
    db = get_db()
    roles = db.table("user_roles").select("agency_id, brand_id") \
              .eq("user_id", user["user_id"]).execute().data

    agency_ids = {r["agency_id"] for r in roles if r.get("agency_id")}
    brand_ids = {r["brand_id"] for r in roles if r.get("brand_id")}

    has_access = brand_id in brand_ids
    if not has_access and agency_ids:
        owning_brand = db.table("brands").select("id").eq("id", brand_id) \
                          .in_("agency_id", list(agency_ids)).execute().data
        has_access = bool(owning_brand)

    if not has_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No access to this brand")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    rows = db.table("brand_configs").update(updates).eq("brand_id", brand_id).execute().data
    return rows[0] if rows else {}
