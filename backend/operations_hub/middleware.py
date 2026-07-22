import uuid

from .models import SystemAuditLog


class PanelAuditMiddleware:
    WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.panel_request_id = request_id
        response = self.get_response(request)
        response["X-Request-ID"] = request_id

        if request.path.startswith("/panel/") and request.method in self.WRITE_METHODS:
            try:
                SystemAuditLog.objects.create(
                    actor=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
                    action=f"panel.{request.method.lower()}",
                    level=SystemAuditLog.Level.ERROR if response.status_code >= 400 else SystemAuditLog.Level.INFO,
                    method=request.method,
                    path=request.path[:500],
                    status_code=response.status_code,
                    message="عملیات ثبت‌شده در پنل Velzon",
                    metadata={
                        "query": request.GET.dict(),
                        "content_type": request.content_type or "",
                    },
                    ip_address=self._ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
                    request_id=request_id,
                )
            except Exception:
                pass

        return response
