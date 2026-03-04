"""Refresh token model for token rotation."""

import hashlib
import secrets
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional
from app.models.database import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)

REFRESH_TOKEN_BYTES = 32  # 256-bit random token


class RefreshToken:
    """Server-side refresh token management with rotation and family-based revocation."""

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        """Hash a raw token string using SHA-256."""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def create(
        user_id: str,
        ip_address: Optional[str] = None,
        family_id: Optional[str] = None,
    ) -> tuple[str, dict]:
        """
        Create a new refresh token.

        Returns (raw_token, record_dict). The raw_token is sent to the client;
        only the SHA-256 hash is stored in the database.
        """
        raw_token = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
        token_hash = RefreshToken._hash_token(raw_token)
        family = family_id or str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        conn = get_db()
        try:
            conn.execute(
                """INSERT INTO refresh_tokens
                   (token_hash, user_id, family_id, expires_at, ip_address)
                   VALUES (?, ?, ?, ?, ?)""",
                (token_hash, user_id, family, expires_at.isoformat(), ip_address),
            )
            conn.commit()
            return raw_token, {
                "token_hash": token_hash,
                "user_id": user_id,
                "family_id": family,
                "expires_at": expires_at.isoformat(),
            }
        finally:
            conn.close()

    @staticmethod
    def verify_and_rotate(
        raw_token: str,
        ip_address: Optional[str] = None,
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Verify a refresh token and rotate it.

        Returns (new_raw_token, user_id, family_id) on success,
        or (None, None, None) on failure.

        Theft detection: if the token was already revoked (reuse),
        the entire token family is revoked.
        """
        token_hash = RefreshToken._hash_token(raw_token)

        conn = get_db()
        try:
            row = conn.execute(
                "SELECT * FROM refresh_tokens WHERE token_hash = ?",
                (token_hash,),
            ).fetchone()

            if not row:
                return None, None, None

            record = dict(row)

            # Theft detection: token already revoked but being reused
            if record["revoked_at"] is not None:
                logger.warning(
                    "Refresh token reuse detected for family %s, user %s. Revoking family.",
                    record["family_id"],
                    record["user_id"],
                )
                conn.execute(
                    "UPDATE refresh_tokens SET revoked_at = ? "
                    "WHERE family_id = ? AND revoked_at IS NULL",
                    (datetime.utcnow().isoformat(), record["family_id"]),
                )
                conn.commit()
                return None, None, None

            # Check expiry
            expires_at = datetime.fromisoformat(record["expires_at"])
            if datetime.utcnow() > expires_at:
                conn.execute(
                    "UPDATE refresh_tokens SET revoked_at = ? WHERE token_hash = ?",
                    (datetime.utcnow().isoformat(), token_hash),
                )
                conn.commit()
                return None, None, None

            # Rotate: revoke old token, create new one in same family
            now = datetime.utcnow()
            new_raw_token = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
            new_hash = RefreshToken._hash_token(new_raw_token)
            new_expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

            # Revoke old, point to new
            conn.execute(
                "UPDATE refresh_tokens SET revoked_at = ?, replaced_by_hash = ? "
                "WHERE token_hash = ?",
                (now.isoformat(), new_hash, token_hash),
            )

            # Insert new token in same family
            conn.execute(
                """INSERT INTO refresh_tokens
                   (token_hash, user_id, family_id, expires_at, ip_address)
                   VALUES (?, ?, ?, ?, ?)""",
                (new_hash, record["user_id"], record["family_id"],
                 new_expires.isoformat(), ip_address),
            )
            conn.commit()

            return new_raw_token, record["user_id"], record["family_id"]
        finally:
            conn.close()

    @staticmethod
    def revoke_all_for_user(user_id: str) -> int:
        """Revoke all active refresh tokens for a user. Returns count revoked."""
        conn = get_db()
        try:
            cursor = conn.execute(
                "UPDATE refresh_tokens SET revoked_at = ? "
                "WHERE user_id = ? AND revoked_at IS NULL",
                (datetime.utcnow().isoformat(), user_id),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    @staticmethod
    def revoke_family(family_id: str) -> int:
        """Revoke all tokens in a family. Returns count revoked."""
        conn = get_db()
        try:
            cursor = conn.execute(
                "UPDATE refresh_tokens SET revoked_at = ? "
                "WHERE family_id = ? AND revoked_at IS NULL",
                (datetime.utcnow().isoformat(), family_id),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    @staticmethod
    def cleanup_expired(days_old: int = 30) -> int:
        """Delete tokens that expired more than days_old days ago."""
        cutoff = (datetime.utcnow() - timedelta(days=days_old)).isoformat()
        conn = get_db()
        try:
            cursor = conn.execute(
                "DELETE FROM refresh_tokens WHERE expires_at < ?",
                (cutoff,),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
