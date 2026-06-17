"""
Creates one test user per role and assigns them in user_roles.
Run once: python scripts/create_test_users.py
"""
import httpx
from supabase import create_client

SUPABASE_URL = "https://nvyrjfvuaqquixunpmdu.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52eXJqZnZ1YXFxdWl4dW5wbWR1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MTUzNjU0MywiZXhwIjoyMDk3MTEyNTQzfQ.-Ue5OrX8g-nUt54frC_NTmMYPCbh_bolE21YMwRGJgY"

db = create_client(SUPABASE_URL, SERVICE_KEY)

# Fetch first agency and first brand for scoped roles
agency = db.table("agencies").select("id, name").limit(1).execute().data[0]
brand  = db.table("brands").select("id, name").limit(1).execute().data[0]

USERS = [
    {
        "email":    "test.master@mediasense.dev",
        "password": "MediaSense#Master2026",
        "role":     "master_admin",
        "scope":    {},
    },
    {
        "email":    "test.agencyadmin@mediasense.dev",
        "password": "MediaSense#AgencyAdmin2026",
        "role":     "agency_admin",
        "scope":    {"agency_id": agency["id"]},
    },
    {
        "email":    "test.analyst@mediasense.dev",
        "password": "MediaSense#Analyst2026",
        "role":     "agency_analyst",
        "scope":    {"agency_id": agency["id"]},
    },
    {
        "email":    "test.brandadmin@mediasense.dev",
        "password": "MediaSense#BrandAdmin2026",
        "role":     "brand_admin",
        "scope":    {"brand_id": brand["id"]},
    },
    {
        "email":    "test.viewer@mediasense.dev",
        "password": "MediaSense#Viewer2026",
        "role":     "brand_viewer",
        "scope":    {"brand_id": brand["id"]},
    },
]

headers = {
    "Authorization": f"Bearer {SERVICE_KEY}",
    "apikey": SERVICE_KEY,
    "Content-Type": "application/json",
}

print(f"\nAgency : {agency['name']} ({agency['id'][:8]}...)")
print(f"Brand  : {brand['name']}  ({brand['id'][:8]}...)\n")
print("-" * 70)


def get_or_create_user(email: str, password: str) -> tuple[str, str]:
    """Returns (user_id, status). Creates user if not exists."""
    # Try to create
    resp = httpx.post(
        f"{SUPABASE_URL}/auth/v1/admin/users",
        headers=headers,
        json={"email": email, "password": password, "email_confirm": True},
    )
    if resp.status_code in (200, 201):
        return resp.json()["id"], "created"

    # Already exists — find via admin list (filter by email)
    list_resp = httpx.get(
        f"{SUPABASE_URL}/auth/v1/admin/users",
        headers=headers,
        params={"page": 1, "per_page": 1000},
    )
    users = list_resp.json().get("users", [])
    match = next((u for u in users if u["email"] == email), None)
    if match:
        return match["id"], "already exists"

    raise RuntimeError(f"Could not create or find user {email}: {resp.text}")


for u in USERS:
    try:
        user_id, status = get_or_create_user(u["email"], u["password"])
    except RuntimeError as e:
        print(f"  FAILED: {e}")
        continue

    # Insert role — skip if already assigned
    role_row = {"user_id": user_id, "role": u["role"], **u["scope"]}
    try:
        db.table("user_roles").insert(role_row).execute()
    except Exception:
        pass  # role already assigned

    print(f"  [{status:14s}]  {u['role']:18s}  {u['email']}")
    print(f"  {'':16s}  password : {u['password']}")
    print()

print("-" * 70)
print("Done.")
