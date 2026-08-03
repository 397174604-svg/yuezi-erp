#!/usr/bin/env python3
"""Focused F052 account write tests without modifying the local database."""

from __future__ import annotations

import os
import sys
from unittest.mock import Mock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, "server")
if SERVER not in sys.path:
    sys.path.insert(0, SERVER)

import mvp_api  # noqa: E402


class FakeCursor:
    def __init__(self, statements: list[tuple[str, tuple | list]]):
        self.statements = statements
        self.lastrowid = 88

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=()):
        self.statements.append((" ".join(sql.split()), params))


class FakeConnection:
    def __init__(self):
        self.statements: list[tuple[str, tuple | list]] = []
        self.commits = 0

    def cursor(self):
        return FakeCursor(self.statements)

    def commit(self):
        self.commits += 1


def handler_for_test():
    handler = object.__new__(mvp_api.MvpRequestHandler)
    handler._require_foundation_write = Mock()
    handler._foundation_store_id = Mock(return_value=1)
    handler._require_selected_write_store = Mock()
    handler._foundation_status = Mock(return_value="ACTIVE")
    handler._allowed_store = Mock(return_value=1)
    handler._audit = Mock()
    handler._success = lambda data: {"code": 20000, "data": data}
    return handler


def test_create_writes_account_role_store_and_audit():
    handler = handler_for_test()
    connection = FakeConnection()
    user = {"tenant_id": 1, "user_id": 1}
    body = {
        "username": "wangwu",
        "name": "王五",
        "initialPassword": "safe1234",
        "roleId": 6,
        "storeId": 1,
        "selectedStoreId": 1,
        "status": "启用",
    }
    with patch.object(
        mvp_api,
        "execute_one",
        side_effect=[{"role_id": 6, "name": "销售"}, None, None],
    ), patch.object(
        mvp_api,
        "execute_all",
        return_value=[{"staff_id": 9, "name": "王五"}],
    ):
        result = handler._save_foundation_user(connection, user, body)

    sql = "\n".join(statement for statement, _ in connection.statements)
    assert "INSERT INTO user_accounts" in sql
    assert "INSERT INTO user_roles" in sql
    assert "INSERT INTO user_stores" in sql
    assert connection.commits == 1
    assert result["data"] == {"id": 88, "saved": True}
    handler._audit.assert_called_once()
    account_params = next(
        params for statement, params in connection.statements
        if "INSERT INTO user_accounts" in statement
    )
    assert str(account_params[3]).startswith("pbkdf2_sha256$")
    assert "safe1234" not in str(account_params[3])


def test_edit_preserves_password_and_same_role_assignment():
    handler = handler_for_test()
    connection = FakeConnection()
    user = {"tenant_id": 1, "user_id": 1}
    body = {
        "id": 46,
        "username": "hanxin",
        "name": "韩新",
        "roleId": 6,
        "storeId": 1,
        "selectedStoreId": 1,
        "status": "启用",
    }
    with patch.object(
        mvp_api,
        "execute_one",
        side_effect=[
            {"role_id": 6, "name": "销售"},
            {"user_id": 46, "staff_id": 3, "username": "hanxin", "default_store_id": 1, "status": "ACTIVE"},
            None,
            None,
            {"role_id": 6},
        ],
    ), patch.object(
        mvp_api,
        "execute_all",
        return_value=[{"staff_id": 3, "name": "韩新"}],
    ):
        handler._save_foundation_user(connection, user, body)

    sql = "\n".join(statement for statement, _ in connection.statements)
    assert "UPDATE user_accounts" in sql
    assert "password_hash" not in sql
    assert "INSERT INTO user_roles" not in sql
    assert "INSERT INTO user_stores" in sql
    assert connection.commits == 1


if __name__ == "__main__":
    test_create_writes_account_role_store_and_audit()
    test_edit_preserves_password_and_same_role_assignment()
    print("F052 foundation user account tests: 2 passed")
