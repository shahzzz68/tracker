import sqlite3

import pytest
from flask import Flask

from database.db import get_db, init_db, seed_db


@pytest.fixture
def ctx(tmp_path):
    app = Flask(__name__)
    app.config["DATABASE"] = str(tmp_path / "test.db")
    with app.app_context():
        yield app


def test_init_db_creates_tables_and_is_idempotent(ctx):
    init_db()
    init_db()
    conn = get_db()
    tables = {
        r["name"]
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()
    assert {"users", "expenses"} <= tables


def test_get_db_row_factory_and_foreign_keys(ctx):
    init_db()
    conn = get_db()
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert isinstance(conn.execute("SELECT 1 AS x").fetchone(), sqlite3.Row)
    conn.close()


def test_expense_requires_existing_user(ctx):
    init_db()
    conn = get_db()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date)"
            " VALUES (999, 5, 'Food', '2026-01-01')"
        )
    conn.close()


def test_duplicate_email_rejected(ctx):
    init_db()
    conn = get_db()
    conn.execute("INSERT INTO users (name, email, password_hash) VALUES ('a', 'a@x.com', 'h')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO users (name, email, password_hash) VALUES ('b', 'a@x.com', 'h')")
    conn.close()


def test_seed_db_is_idempotent_and_hashes_password(ctx):
    init_db()
    seed_db()
    conn = get_db()
    users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    expenses = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    conn.close()
    assert users == 1 and expenses > 0

    seed_db()
    conn = get_db()
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == users
    assert conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == expenses
    pw = conn.execute("SELECT password_hash FROM users").fetchone()[0]
    conn.close()
    assert pw != "demo1234"
