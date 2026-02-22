"""Audit logging model."""

import json
import logging
from typing import Any, Dict, List, Optional
from app.models.database import get_db

logger = logging.getLogger(__name__)


class AuditLog:
    """Record and retrieve audit trail entries."""

    @staticmethod
    def log(
        action: str,
        resource_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ):
        """Insert an audit log entry.

        This method never raises — audit logging must not break the main
        request flow. Failures are logged via the logger.
        """
        try:
            conn = get_db()
            try:
                conn.execute(
                    """INSERT INTO audit_logs
                       (action, user_id, resource_type, resource_id, details, ip_address)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        action,
                        user_id,
                        resource_type,
                        resource_id,
                        json.dumps(details) if details else None,
                        ip_address,
                    ),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:
            logger.error("Failed to write audit log: %s", exc)

    @staticmethod
    def count_today(user_id: str, actions: list[str]) -> int:
        """Count today's audit entries for a user filtered by action types."""
        conn = get_db()
        try:
            placeholders = ",".join("?" for _ in actions)
            row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM audit_logs "
                f"WHERE user_id = ? AND action IN ({placeholders}) "
                f"AND date(logged_at) = date('now')",
                (user_id, *actions),
            ).fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    @staticmethod
    def get_by_user(user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve audit logs for a specific user, newest first."""
        conn = get_db()
        try:
            rows = conn.execute(
                """SELECT log_id, action, user_id, resource_type, resource_id,
                          details, ip_address, logged_at
                   FROM audit_logs
                   WHERE user_id = ?
                   ORDER BY logged_at DESC
                   LIMIT ? OFFSET ?""",
                (user_id, limit, offset),
            ).fetchall()
            return [_row_to_dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_all(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve all audit logs, newest first. For admin use."""
        conn = get_db()
        try:
            rows = conn.execute(
                """SELECT log_id, action, user_id, resource_type, resource_id,
                          details, ip_address, logged_at
                   FROM audit_logs
                   ORDER BY logged_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()
            return [_row_to_dict(row) for row in rows]
        finally:
            conn.close()


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert a sqlite3.Row to a dict, parsing the JSON details field."""
    d = dict(row)
    if d.get("details"):
        try:
            d["details"] = json.loads(d["details"])
        except (json.JSONDecodeError, TypeError):
            pass
    return d
