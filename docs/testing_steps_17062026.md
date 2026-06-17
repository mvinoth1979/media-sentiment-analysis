# Wave 3 Testing Checklist — 17 Jun 2026

End-to-end verification steps for Wave 3: auth guard, CSV export, email alerts, self-serve brand onboarding.

---

## Pre-flight

- [ ] Migration 010 applied in Supabase SQL editor
- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] `RESEND_API_KEY` set in Railway environment variables

---

## 1. Migration 010 (Supabase)

**Run:** Paste `supabase/migrations/010_alert_configs.sql` into Supabase SQL editor → Run

**Verify:**
```sql
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'alert_configs' ORDER BY ordinal_position;
```
Expected: 8 rows — id, brand_id, alert_type, threshold, notify_email, enabled, last_triggered_at, created_at

- [ ] Table exists with correct columns
- [ ] Index `idx_alert_configs_brand` created

---

## 2. Pipeline Trigger Auth Guard (Step 1)

**Unauthenticated — must be rejected:**
```bash
curl -X POST https://<railway-url>/pipeline/trigger
# Expected: 401 or 403
```

**Authenticated master_admin — must succeed:**
```bash
# Get JWT: browser devtools → Application → Local Storage → supabase auth token
curl -X POST https://<railway-url>/pipeline/trigger \
  -H "Authorization: Bearer <your-jwt>"
# Expected: {"status": "enqueued"}
```

- [ ] Unauthenticated POST → 401/403
- [ ] Authenticated master_admin POST → `{"status": "enqueued"}`

---

## 3. CSV Export (Step 2)

**In the app:**
1. Go to Mentions tab → apply a filter (e.g. sentiment = negative)
2. Click **Export CSV** button (top right of mentions list)
3. Open downloaded file — all rows must match the active filter
4. Check array columns (topics, entities, keywords, states_mentioned) are pipe-separated: `politics|economy`

**Direct API test:**
```bash
curl "https://<railway-url>/dashboard/export/<brand-id>?sentiment=negative" \
  -H "Authorization: Bearer <jwt>" -o test.csv
head -5 test.csv
```

- [ ] Export button visible in Mentions header
- [ ] Downloaded file is valid CSV with header row
- [ ] Filter is respected in exported rows
- [ ] Array fields use `|` separator
- [ ] Unauthenticated GET → 401

---

## 4. Email Alerts (Step 3)

**Prerequisite:** `RESEND_API_KEY` must be set in Railway.

**Create a test alert that always fires:**
1. Log in as admin → select any brand → Overview → scroll to bottom → **Email Alerts** section
2. Set: type = `Perception score below`, threshold = `99`, email = your address
3. Click **+ Add Alert** — alert row should appear immediately
4. Trigger the pipeline: `POST /pipeline/trigger` with your JWT
5. Wait ~2 minutes → check inbox for MediaSense alert email

**Verify 4-hour cooldown:**
- Trigger pipeline again immediately after first email
- No second email should arrive within 4 hours

**Verify delete:**
- Click `×` next to the alert → row disappears
- Trigger pipeline → no email sent

- [ ] Alert form visible in Overview (admin login only)
- [ ] Alert row appears after creation
- [ ] Email received after pipeline run (within 2 min)
- [ ] Second trigger within 4h — no duplicate email
- [ ] Delete removes the alert row
- [ ] After delete, pipeline run sends no email

---

## 5. Self-serve Brand Onboarding (Step 4a — Brand Creation)

**Wizard flow:**
1. Log in as `master_admin` or `agency_admin`
2. From Brand Search screen → click **Add Brand** (top right, `+` icon)
3. Step 1: Enter brand name (e.g. `Test Brand`) → Next
4. Step 2: Add keywords — type each, press Enter (e.g. `TestCo`, `Test Corp`) → Next
5. Step 3: Check `English` + at least one other language → **Create Brand**
6. Should auto-navigate to the new brand's Overview tab

**Verify in Supabase:**
```sql
SELECT b.name, bc.keywords, bc.languages
FROM brands b JOIN brand_configs bc ON bc.brand_id = b.id
WHERE b.name = 'Test Brand';
```

- [ ] Add Brand button visible for agency_admin / master_admin
- [ ] 3-step wizard modal opens and progresses correctly
- [ ] New brand appears in brand picker after creation
- [ ] `brand_configs` row exists with correct keywords and languages
- [ ] Add Brand button NOT visible when logged in as brand_viewer

---

## 6. User Invite (Step 4b — User Management)

**Invite flow:**
1. Select any brand → click **Users** tab in top nav
2. Enter an email address you control
3. Select role = `brand_viewer`
4. Click **Send Invite**
5. Check that email — should receive a Supabase magic-link
6. Click the link → logs in → brand picker should show only that brand
7. Verify Users tab shows the new user with `brand viewer` badge

**Verify role gating:**
- Log in as `brand_viewer` → **Users** tab must NOT appear in nav
- Log in as `brand_viewer` → **Add Brand** button must NOT appear on Brand Search

- [ ] Users tab visible for agency_admin / master_admin
- [ ] Invite form accepts email + role selection
- [ ] Magic-link email received by invitee
- [ ] Invitee can log in and sees only the assigned brand
- [ ] New user row appears in Users tab with correct role badge
- [ ] Users tab NOT visible for brand_viewer role
- [ ] Add Brand NOT visible for brand_viewer role

---

## Quick Smoke-Test Sequence (5 minutes)

| # | Action | Expected |
|---|--------|----------|
| 1 | Run SQL migration | `alert_configs` table exists |
| 2 | Unauthenticated POST `/pipeline/trigger` | 401/403 |
| 3 | Authenticated POST `/pipeline/trigger` | `{"status":"enqueued"}` |
| 4 | Export CSV with sentiment=negative filter | All rows negative, pipe-separated arrays |
| 5 | Create alert (threshold=99) → trigger pipeline | Alert email received |
| 6 | Delete alert → trigger pipeline | No email sent |
| 7 | Add Brand wizard (3 steps) | New brand in picker, DB row created |
| 8 | Invite user → magic-link login | Invitee sees only assigned brand |
| 9 | Login as brand_viewer | No Add Brand button, no Users tab |

---

## Known Conditions

- Alert emails are silently skipped if `RESEND_API_KEY` is missing in Railway — no error thrown
- Alert cooldown is 4 hours per alert config row (`last_triggered_at` column)
- Brand creation auto-selects the first agency for `master_admin` accounts with no direct agency assignment
- The Users tab lists only brand-scoped `user_roles` rows — agency-level users appear via their agency role but are not listed here
