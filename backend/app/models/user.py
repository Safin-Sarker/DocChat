"""User model with password hashing."""

import uuid
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
