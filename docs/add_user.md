# Adding Users to MediaSense

## Step 1 — Create the account in Supabase

Go to **Supabase Dashboard → Authentication → Users**

**Option A — Invite by email (recommended)**
- Click **"Invite user"**
- Enter their email address
- They receive an email with a sign-in link
- After they accept, find their `id` in the Users list

**Option B — Create manually with password**
- Click **"Add user"**
- Enter email + password directly
- Account is created instantly (no email sent)
- Find their `id` in the Users list

---

## Step 2 — Find their user ID

Run this in **Supabase SQL Editor**:

```sql
SELECT id, email FROM auth.users;
```

Copy the `id` next to their email address.

---

## Step 3 — Assign a role

Run the appropriate INSERT in **Supabase SQL Editor** based on the access level needed.

### Brand-level access (scoped to one brand)

```sql
INSERT INTO user_roles (user_id, brand_id, role)
VALUES (
  '<their-user-id>',
  '<brand-id>',
  'brand_viewer'   -- or brand_admin
);
```

### Agency-level access (covers all brands under the agency)

```sql
INSERT INTO user_roles (user_id, agency_id, role)
VALUES (
  '<their-user-id>',
  '<agency-id>',
  'agency_analyst'  -- or agency_admin
);
```

### Platform-wide master admin (delete rights + full access)

```sql
INSERT INTO user_roles (user_id, role)
VALUES (
  '<their-user-id>',
  'master_admin'
);
```

---

## Role reference

| Role | Scope | Permissions |
|------|-------|-------------|
| `brand_viewer` | One brand | Read-only: overview, mentions, sources, topics |
| `brand_admin` | One brand | Read + update brand config |
| `agency_analyst` | All brands in agency | Read across all agency brands |
| `agency_admin` | All brands in agency | Read + update config across all agency brands |
| `master_admin` | Platform-wide | Everything including delete mentions |

---

## Useful lookup queries

```sql
-- Find all agencies
SELECT id, name FROM agencies;

-- Find all brands
SELECT id, name, agency_id FROM brands;

-- List all users and their roles
SELECT au.email, ur.role, ur.brand_id, ur.agency_id
FROM user_roles ur
JOIN auth.users au ON au.id = ur.user_id
ORDER BY au.email;

-- Verify master_admin assignment
SELECT ur.user_id, ur.role, au.email
FROM user_roles ur
JOIN auth.users au ON au.id = ur.user_id
WHERE ur.role = 'master_admin';
```

---

## Removing access

```sql
-- Remove a specific role from a user
DELETE FROM user_roles
WHERE user_id = '<their-user-id>'
  AND role = 'brand_viewer';

-- Remove all roles from a user
DELETE FROM user_roles
WHERE user_id = '<their-user-id>';
```
