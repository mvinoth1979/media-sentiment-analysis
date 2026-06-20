from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.auth.dependencies import get_current_user, require_brand_role, require_role, WRITE_ROLES
from app.storage.postgres import get_db
from app.config import settings

router = APIRouter()


class BrandConfigUpdate(BaseModel):
    keywords: list[str] | None = None
    languages: list[str] | None = None
    states: list[str] | None = None
    competitors: list[str] | None = None
    portal_ids: list[str] | None = None
    youtube_enabled: bool | None = None
    youtube_channel_ids: list[str] | None = None
    reddit_enabled: bool | None = None
    reddit_subreddits: list[str] | None = None


@router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    return user


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


class BrandCreate(BaseModel):
    name: str
    keywords: list[str]
    languages: list[str] = ["en"]
    youtube_enabled: bool = False
    youtube_channel_ids: list[str] = []
    reddit_enabled: bool = False
    reddit_subreddits: list[str] = []


@router.post("/brands", status_code=201)
def create_brand(
    payload: BrandCreate,
    user: dict = Depends(require_role("agency_admin", "master_admin")),
):
    db = get_db()
    roles = db.table("user_roles").select("agency_id, role") \
              .eq("user_id", user["user_id"]).execute().data
    agency_id = next((r["agency_id"] for r in roles if r.get("agency_id")), None)
    if not agency_id:
        # master_admin with no agency: pick the first agency in the system
        first = db.table("agencies").select("id").limit(1).execute().data
        if not first:
            raise HTTPException(400, "No agency found — create one first")
        agency_id = first[0]["id"]
    brand = db.table("brands").insert({"agency_id": agency_id, "name": payload.name}).execute().data[0]
    db.table("brand_configs").insert({
        "brand_id":           brand["id"],
        "keywords":           payload.keywords,
        "languages":          payload.languages,
        "youtube_enabled":     payload.youtube_enabled,
        "youtube_channel_ids": payload.youtube_channel_ids,
        "reddit_enabled":      payload.reddit_enabled,
        "reddit_subreddits":   payload.reddit_subreddits,
    }).execute()
    return brand


class UserInvite(BaseModel):
    email: str
    role: str
    brand_id: str | None = None


@router.post("/users/invite")
def invite_user(
    payload: UserInvite,
    user: dict = Depends(require_role("agency_admin", "master_admin")),
):
    from supabase import create_client
    admin = create_client(settings.supabase_url, settings.supabase_service_role_key)
    try:
        invited = admin.auth.admin.invite_user_by_email(payload.email)
    except Exception as e:
        raise HTTPException(400, f"Could not invite {payload.email}: {e}")
    db = get_db()
    roles = db.table("user_roles").select("agency_id") \
              .eq("user_id", user["user_id"]).execute().data
    agency_id = next((r["agency_id"] for r in roles if r.get("agency_id")), None)
    role_row: dict = {"user_id": invited.user.id, "role": payload.role}
    if payload.brand_id:
        role_row["brand_id"] = payload.brand_id
    elif agency_id:
        role_row["agency_id"] = agency_id
    else:
        raise HTTPException(400, "Cannot determine agency for role assignment")
    db.table("user_roles").insert(role_row).execute()
    return {"status": "invited", "email": payload.email}


@router.get("/users/{brand_id}")
def list_brand_users(
    brand_id: str,
    _user: dict = Depends(require_brand_role(*WRITE_ROLES)),
):
    db = get_db()
    role_rows = db.table("user_roles").select("id, user_id, role, brand_id, agency_id") \
                  .eq("brand_id", brand_id).execute().data
    # Enrich with email from auth.users via admin API
    from supabase import create_client
    admin = create_client(settings.supabase_url, settings.supabase_service_role_key)
    user_ids = [r["user_id"] for r in role_rows]
    enriched = []
    for row in role_rows:
        try:
            u = admin.auth.admin.get_user_by_id(row["user_id"])
            row["email"] = u.user.email if u and u.user else ""
        except Exception:
            row["email"] = ""
        enriched.append(row)
    return enriched


@router.delete("/brands/{brand_id}", status_code=204)
def delete_brand(
    brand_id: str,
    _user: dict = Depends(require_role("master_admin")),
):
    db = get_db()
    db.table("brands").delete().eq("id", brand_id).execute()


@router.delete("/users/roles/{role_id}", status_code=204)
def delete_user_role(
    role_id: str,
    _user: dict = Depends(require_role("agency_admin", "master_admin")),
):
    db = get_db()
    db.table("user_roles").delete().eq("id", role_id).execute()


@router.get("/brands/{brand_id}/config")
def get_brand_config(
    brand_id: str,
    _user: dict = Depends(require_brand_role(*WRITE_ROLES)),
):
    db = get_db()
    rows = db.table("brand_configs").select("*").eq("brand_id", brand_id).execute().data
    return rows[0] if rows else {}


@router.put("/brands/{brand_id}/config")
def update_brand_config(
    brand_id: str,
    payload: BrandConfigUpdate,
    _user: dict = Depends(require_brand_role(*WRITE_ROLES)),
):
    db = get_db()
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    rows = db.table("brand_configs").update(updates).eq("brand_id", brand_id).execute().data
    return rows[0] if rows else {}
