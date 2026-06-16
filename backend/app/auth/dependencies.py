import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.storage.postgres import get_db

bearer = HTTPBearer()


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


def require_role(*allowed_roles: str):
    """Dependency factory: restrict an endpoint to users holding one of allowed_roles."""
    def checker(user: dict = Depends(get_current_user)) -> dict:
        user_role_names = {r["role"] for r in user["roles"]}
        if not user_role_names & set(allowed_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Insufficient role for this action")
        return user
    return checker
