from fastapi import Depends, HTTPException, status
from app.auth.dependencies import get_current_user
from app.storage.postgres import get_db


def require_brand_access(brand_id: str, user: dict = Depends(get_current_user)) -> dict:
    """Dependency: restrict a {brand_id}-scoped route to users granted that brand
    directly or via the agency that owns it."""
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
    return user
