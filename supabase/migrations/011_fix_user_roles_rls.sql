-- Fix: remove self-referential subquery from user_roles RLS policy.
-- The original policy queried user_roles inside itself, causing infinite
-- recursion and a 500 from PostgREST for any frontend SELECT on user_roles.
-- The backend uses the service-role key and bypasses RLS entirely, so this
-- simpler policy is sufficient: each user can only see their own role rows.

DROP POLICY IF EXISTS "users can view their own role assignments" ON user_roles;

CREATE POLICY "users can view their own role assignments"
ON user_roles FOR SELECT
USING (user_id = auth.uid());
