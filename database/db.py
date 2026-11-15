import os
import sqlite3
from datetime import date, timedelta

from flask import current_app, has_app_context
from werkzeug.security import generate_password_hash

DEFAULT_DATABASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "expense_tracker.db",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount      REAL NOT NULL CHECK (amount > 0),
    category    TEXT NOT NULL,
    description TEXT,
    date        TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses (user_id, date);
"""


def _database_path():
    if has_app_context():
        return current_app.config.get("DATABASE", DEFAULT_DATABASE)
    return DEFAULT_DATABASE


def get_db():
    conn = sqlite3.connect(_database_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    try:
        if conn.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            return

        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@example.com", generate_password_hash("demo1234", method="pbkdf2:sha256")),
        )
        user_id = cur.lastrowid

        today = date.today()
        samples = [
            (12.50, "Food", "Lunch", 0),
            (45.00, "Groceries", "Weekly shop", 1),
            (30.00, "Transport", "Fuel", 2),
            (9.99, "Entertainment", "Streaming subscription", 4),
            (120.00, "Bills", "Electricity", 6),
            (18.75, "Food", "Dinner out", 8),
            (60.00, "Shopping", "Clothes", 11),
            (25.00, "Health", "Pharmacy", 15),
            (7.20, "Transport", "Bus pass top-up", 20),
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, description, date)"
            " VALUES (?, ?, ?, ?, ?)",
            [
                (user_id, amount, category, desc, (today - timedelta(days=ago)).isoformat())
                for amount, category, desc, ago in samples
            ],
        )
        conn.commit()
    finally:
        conn.close()
