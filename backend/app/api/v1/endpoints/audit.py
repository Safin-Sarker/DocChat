"""Audit log endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from starlette.requests import Request
from app.core.auth import get_current_user, get_current_admin
from app.core.config import settings
from app.core.limiter import limiter
from app.models.audit_log import AuditLog

router = APIRouter()


@router.get("/me", response_model=List[Dict[str, Any]])
@limiter.limit("30/minute")
async def get_my_audit_logs(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Get audit logs for the current user."""
    return AuditLog.get_by_user(current_user["user_id"], limit=limit, offset=offset)


@router.get("/", response_model=List[Dict[str, Any]])
@limiter.limit("30/minute")
async def get_all_audit_logs(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_admin),
):
    """Get all audit logs (admin only)."""
    return AuditLog.get_all(limit=limit, offset=offset)
