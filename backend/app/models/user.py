"""User model with password hashing."""

import uuid
import secrets
import re
import bcrypt
from .database import get_db


class User:
    """User model for authentication."""

    @staticmethod
    def create(email: str, username: str, password: str) -> dict:
        """Create a new user with hashed password."""
        user_id = str(uuid.uuid4())
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (user_id, email, username, password_hash) VALUES (?, ?, ?, ?)",
                (user_id, email.lower(), username, password_hash)
            )
            conn.commit()
            return {"user_id": user_id, "email": email.lower(), "username": username}
        finally:
            conn.close()

    @staticmethod
    def authenticate(email: str, password: str) -> dict | None:
        """Authenticate user by email and password."""
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email.lower(),)
            ).fetchone()

            if row and bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
                return {
                    "user_id": row["user_id"],
                    "email": row["email"],
                    "username": row["username"]
                }
            return None
        finally:
            conn.close()

    @staticmethod
    def get_by_id(user_id: str) -> dict | None:
        """Get user by ID."""
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT user_id, email, username, created_at FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def get_by_email(email: str) -> dict | None:
        """Get user by email."""
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT user_id, email, username, created_at FROM users WHERE email = ?",
                (email.lower(),)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def exists(email: str = None, username: str = None) -> bool:
        """Check if user exists by email or username."""
        conn = get_db()
        try:
            if email:
                row = conn.execute(
                    "SELECT 1 FROM users WHERE email = ?",
                    (email.lower(),)
                ).fetchone()
                if row:
                    return True
            if username:
                row = conn.execute(
                    "SELECT 1 FROM users WHERE username = ?",
                    (username,)
                ).fetchone()
                if row:
                    return True
            return False
        finally:
            conn.close()

    @staticmethod
    def get_by_oauth(provider: str, provider_user_id: str) -> dict | None:
        """Get user by OAuth provider account."""
        conn = get_db()
        try:
            row = conn.execute(
                """
                SELECT u.user_id, u.email, u.username, u.created_at
                FROM oauth_accounts oa
                JOIN users u ON u.user_id = oa.user_id
                WHERE oa.provider = ? AND oa.provider_user_id = ?
                """,
                (provider, provider_user_id)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def link_oauth_account(
        user_id: str,
        provider: str,
        provider_user_id: str,
        email: str | None = None
    ) -> None:
        """Link OAuth account to a user (idempotent)."""
        conn = get_db()
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO oauth_accounts (user_id, provider, provider_user_id, email)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, provider, provider_user_id, (email or "").lower() or None)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _slugify_username(raw: str) -> str:
        value = (raw or "").strip().lower()
        value = re.sub(r"[^a-z0-9_]+", "_", value)
        value = re.sub(r"_+", "_", value).strip("_")
        if len(value) < 3:
            value = f"user_{secrets.token_hex(2)}"
        return value[:40]

    @staticmethod
    def _generate_unique_username(base: str) -> str:
        candidate = base
        conn = get_db()
        try:
            suffix = 1
            while True:
                row = conn.execute(
                    "SELECT 1 FROM users WHERE username = ?",
                    (candidate,)
                ).fetchone()
                if not row:
                    return candidate
                suffix += 1
                candidate = f"{base[:35]}_{suffix}"
        finally:
            conn.close()

    @staticmethod
    def find_or_create_from_oauth(
        provider: str,
        provider_user_id: str,
        email: str | None,
        display_name: str | None
    ) -> dict:
        """Find existing user or create a new one from OAuth identity."""
        existing_oauth_user = User.get_by_oauth(provider, provider_user_id)
        if existing_oauth_user:
            return existing_oauth_user

        normalized_email = (email or "").strip().lower()
        if not normalized_email:
            normalized_email = f"{provider}_{provider_user_id}@oauth.local"

        user = User.get_by_email(normalized_email)
        if user:
            User.link_oauth_account(
                user_id=user["user_id"],
                provider=provider,
                provider_user_id=provider_user_id,
                email=normalized_email,
            )
            return user

        base_username = User._slugify_username(display_name or normalized_email.split("@")[0])
        username = User._generate_unique_username(base_username)
        random_password = secrets.token_urlsafe(32)
        new_user = User.create(
            email=normalized_email,
            username=username,
            password=random_password
        )
        User.link_oauth_account(
            user_id=new_user["user_id"],
            provider=provider,
            provider_user_id=provider_user_id,
            email=normalized_email,
        )
        return new_user
