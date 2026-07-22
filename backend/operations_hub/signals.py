from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from .models import SystemAuditLog


def _safe_text(value):
    return str(value or "")


def _request_value(request, attribute):
    if request is None:
        return ""
    return _safe_text(getattr(request, attribute, ""))


def _meta_value(request, key):
    if request is None:
        return ""
    return _safe_text(getattr(request, "META", {}).get(key, ""))


def _ip(request):
    if request is None:
        return None

    meta = getattr(request, "META", {}) or {}
    forwarded = _safe_text(meta.get("HTTP_X_FORWARDED_FOR", ""))

    if forwarded:
        return forwarded.split(",")[0].strip() or None

    return _safe_text(meta.get("REMOTE_ADDR", "")) or None


def _write_audit(**kwargs):
    """Audit must never break authentication or the requested operation."""
    defaults = {
        "actor": None,
        "action": "",
        "level": SystemAuditLog.Level.INFO,
        "method": "",
        "path": "",
        "status_code": None,
        "target_type": "",
        "target_id": "",
        "message": "",
        "metadata": {},
        "ip_address": None,
        "user_agent": "",
        "request_id": "",
    }
    defaults.update(kwargs)

    # Explicitly normalize every NOT NULL string/JSON field.
    for key in (
        "action",
        "level",
        "method",
        "path",
        "target_type",
        "target_id",
        "message",
        "user_agent",
        "request_id",
    ):
        defaults[key] = _safe_text(defaults.get(key))

    defaults["metadata"] = defaults.get("metadata") or {}

    try:
        SystemAuditLog.objects.create(**defaults)
    except Exception:
        # An audit failure must never prevent login, logout, API or panel access.
        return None


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    _write_audit(
        actor=user,
        action="auth.login",
        level=SystemAuditLog.Level.SECURITY,
        method=_request_value(request, "method"),
        path=_request_value(request, "path"),
        message="ورود موفق کاربر",
        ip_address=_ip(request),
        user_agent=_meta_value(request, "HTTP_USER_AGENT"),
        request_id=_safe_text(getattr(request, "panel_request_id", "")) if request else "",
    )


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    _write_audit(
        actor=user if getattr(user, "pk", None) else None,
        action="auth.logout",
        level=SystemAuditLog.Level.SECURITY,
        method=_request_value(request, "method"),
        path=_request_value(request, "path"),
        message="خروج کاربر",
        ip_address=_ip(request),
        user_agent=_meta_value(request, "HTTP_USER_AGENT"),
        request_id=_safe_text(getattr(request, "panel_request_id", "")) if request else "",
    )


@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs):
    credentials = credentials or {}
    username = _safe_text(credentials.get("username", ""))

    _write_audit(
        action="auth.login_failed",
        level=SystemAuditLog.Level.WARNING,
        method=_request_value(request, "method"),
        path=_request_value(request, "path"),
        message=f"ورود ناموفق برای {username}",
        metadata={"username": username},
        ip_address=_ip(request),
        user_agent=_meta_value(request, "HTTP_USER_AGENT"),
        request_id=_safe_text(getattr(request, "panel_request_id", "")) if request else "",
    )
