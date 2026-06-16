import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows

    def select(self, *_a, **_k):
        return self

    def eq(self, col, val):
        self._rows = [r for r in self._rows if r.get(col) == val]
        return self

    def execute(self):
        return SimpleNamespace(data=self._rows)


class _FakeDB:
    def __init__(self, tables):
        self._tables = tables

    def table(self, name):
        return _FakeQuery(list(self._tables.get(name, [])))


def _creds():
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-123")


def _fake_supabase_response():
    return SimpleNamespace(status_code=200, json=lambda: {"id": "user-1", "email": "t@t.com"})


def test_get_current_user_attaches_roles():
    from app.auth.dependencies import get_current_user

    roles = [{"user_id": "user-1", "agency_id": "agency-1", "brand_id": None, "role": "agency_admin"}]
    fake_db = _FakeDB({"user_roles": roles})

    with patch("app.auth.dependencies.httpx.get", return_value=_fake_supabase_response()), \
         patch("app.auth.dependencies.get_db", return_value=fake_db):
        user = asyncio.run(get_current_user(_creds()))

    assert user["user_id"] == "user-1"
    assert user["roles"] == roles


def test_get_current_user_with_no_role_grants_returns_empty_roles():
    from app.auth.dependencies import get_current_user

    fake_db = _FakeDB({"user_roles": []})

    with patch("app.auth.dependencies.httpx.get", return_value=_fake_supabase_response()), \
         patch("app.auth.dependencies.get_db", return_value=fake_db):
        user = asyncio.run(get_current_user(_creds()))

    assert user["roles"] == []


def test_require_role_allows_matching_role():
    from app.auth.dependencies import require_role

    user = {"user_id": "user-1", "email": "t@t.com",
             "roles": [{"role": "agency_admin", "agency_id": "agency-1", "brand_id": None}]}
    checker = require_role("agency_admin", "brand_admin")

    result = checker(user=user)

    assert result is user


def test_require_role_rejects_non_matching_role():
    from app.auth.dependencies import require_role

    user = {"user_id": "user-1", "email": "t@t.com",
             "roles": [{"role": "brand_viewer", "agency_id": None, "brand_id": "brand-1"}]}
    checker = require_role("agency_admin", "brand_admin")

    with pytest.raises(HTTPException) as exc_info:
        checker(user=user)

    assert exc_info.value.status_code == 403


def test_require_role_rejects_user_with_no_roles():
    from app.auth.dependencies import require_role

    user = {"user_id": "user-1", "email": "t@t.com", "roles": []}
    checker = require_role("agency_admin")

    with pytest.raises(HTTPException) as exc_info:
        checker(user=user)

    assert exc_info.value.status_code == 403
