from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponseRedirect
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import SocialAuthExchangeCode
from .serializers import UserSerializer


def _hash_code(raw_code: str) -> str:
    return hashlib.sha256(raw_code.encode("utf-8")).hexdigest()


def _role_redirect(user) -> str:
    role = getattr(user, "role", "") or ""
    if role in {"admin", "support", "supervisor"} or user.is_staff:
        return "/panel/"
    return "/dashboard"


@login_required
def frontend_auth_bridge(request: HttpRequest) -> HttpResponseRedirect:
    callback_url = settings.FRONTEND_AUTH_CALLBACK_URL
    if not request.user.is_active:
        return HttpResponseRedirect(f"{callback_url}?{urlencode({'error': 'account_disabled'})}")

    raw_code = secrets.token_urlsafe(48)
    SocialAuthExchangeCode.objects.create(
        user=request.user,
        code_digest=_hash_code(raw_code),
        expires_at=timezone.now() + timedelta(seconds=settings.SOCIAL_EXCHANGE_CODE_TTL_SECONDS),
        requested_ip=_client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:500],
    )
    return HttpResponseRedirect(f"{callback_url}?{urlencode({'code': raw_code})}")


class SocialAuthExchangeView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    @transaction.atomic
    def post(self, request):
        raw_code = str(request.data.get("code") or "").strip()
        if not raw_code:
            return Response({"code": ["کد ورود ارسال نشده است."]}, status=status.HTTP_400_BAD_REQUEST)

        exchange = (SocialAuthExchangeCode.objects.select_for_update().select_related("user")
                    .filter(code_digest=_hash_code(raw_code)).first())
        if exchange is None:
            return Response({"detail": "کد ورود نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST)
        if exchange.used_at is not None:
            return Response({"detail": "این کد قبلاً استفاده شده است."}, status=status.HTTP_409_CONFLICT)
        if exchange.expires_at <= timezone.now():
            return Response({"detail": "کد ورود منقضی شده است."}, status=status.HTTP_400_BAD_REQUEST)
        if not exchange.user.is_active:
            return Response({"detail": "حساب کاربری غیرفعال است."}, status=status.HTTP_403_FORBIDDEN)

        exchange.used_at = timezone.now()
        exchange.save(update_fields=["used_at"])
        refresh = RefreshToken.for_user(exchange.user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(exchange.user, context={"request": request}).data,
            "redirect_to": _role_redirect(exchange.user),
        })


def _client_ip(request: HttpRequest) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None
