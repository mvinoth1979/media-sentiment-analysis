import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.storage.postgres import get_db

bearer = HTTPBearer()

# Role sets for reuse across routers
READ_ROLES = ("master_admin", "agency_admin", "agency_analyst", "brand_admin", "brand_viewer")
WRITE_ROLES = ("master_admin", "agency_admin", "brand_admin")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    token = credentials.credentials
    resp = httpx.get(
        f"{settings.supabase_url}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": settings.supabase_anon_key,
        },
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token")
    user = resp.json()

    db = get_db()
    roles = db.table("user_roles").select("role, agency_id, brand_id") \
              .eq("user_id", user["id"]).execute().data

    return {"user_id": user["id"], "email": user["email"], "roles": roles}


def require_brand_role(*allowed_roles: str):
    """Combined dependency: verifies brand access AND that the user holds one of
    allowed_roles scoped to the specific brand_id in the path.

    master_admin is a platform-wide superuser and satisfies any role check.
    For all other roles, the check is scoped to the brand being accessed —
    a brand_admin on Brand A cannot satisfy a role check on Brand B.
    """
    def checker(brand_id: str, user: dict = Depends(get_current_user)) -> dict:
        db = get_db()
        roles = db.table("user_roles").select("role, agency_id, brand_id") \
                  .eq("user_id", user["user_id"]).execute().data

        # master_admin: platform-wide superuser, bypasses all brand-level scoping
        if any(r["role"] == "master_admin" for r in roles):
            return user

        agency_ids = {r["agency_id"] for r in roles if r.get("agency_id")}
        direct_brand_roles = {r["brand_id"]: r["role"] for r in roles if r.get("brand_id")}

        # Check direct brand-level role for this specific brand_id
        if brand_id in direct_brand_roles:
            if direct_brand_roles[brand_id] in allowed_roles:
                return user
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Insufficient role for this brand")

        # Check via agency ownership — user's agency role must be in allowed_roles
        # for the agency that specifically owns this brand
        if agency_ids:
            owning = db.table("brands").select("id, agency_id") \
                        .eq("id", brand_id) \
                        .in_("agency_id", list(agency_ids)).execute().data
            if owning:
                owning_agency_id = owning[0]["agency_id"]
                agency_role = next(
                    (r["role"] for r in roles if r.get("agency_id") == owning_agency_id),
                    None,
                )
                if agency_role in allowed_roles:
                    return user
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Insufficient role for this brand")

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No access to this brand")
    return checker


def require_role(*allowed_roles: str):
    """Legacy dependency: non-brand-scoped role check. Prefer require_brand_role
    for brand-scoped endpoints. Kept for non-brand routes."""
    def checker(user: dict = Depends(get_current_user)) -> dict:
        user_role_names = {r["role"] for r in user["roles"]}
        if not user_role_names & set(allowed_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Insufficient role for this action")
        return user
    return checker
