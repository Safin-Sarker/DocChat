"""SQLite database setup for user management."""

import sqlite3
from pathlib import Path

DB_PATH = Path("./data/users.db")


def get_db():
    """Get database connection."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with users and documents tables."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS oauth_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            provider_user_id TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(provider, provider_user_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            pages INTEGER DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            user_id TEXT,
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            details TEXT,
            ip_address TEXT,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_hash TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            family_id TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            revoked_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            replaced_by_hash TEXT,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id
        ON refresh_tokens(user_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_family_id
        ON refresh_tokens(family_id)
    """)

    # Safe migration: add is_admin column to existing users table
    cursor = conn.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if "is_admin" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")

    conn.commit()
    conn.close()
