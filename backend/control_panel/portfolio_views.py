from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import EditorPortfolioItem


def _require_admin(user):
    if not (user.is_superuser or user.is_staff or getattr(user, "role", "") == "admin"):
        raise PermissionDenied


@login_required
def portfolio_moderation(request):
    _require_admin(request.user)
    state = request.GET.get("state", "pending").strip()
    items = EditorPortfolioItem.objects.select_related("editor", "editor__user", "style", "reviewed_by").order_by("-created_at")

    allowed = {choice for choice, _ in EditorPortfolioItem.ReviewStatus.choices}
    if state in allowed:
        items = items.filter(review_status=state)

    return render(request, "control_panel/portfolio_moderation.html", {
        "page_title": "بررسی نمونه‌کار ادیتورها",
        "items": items[:300],
        "selected_state": state,
        "pending_count": EditorPortfolioItem.objects.filter(review_status=EditorPortfolioItem.ReviewStatus.PENDING).count(),
    })


@login_required
@require_POST
def review_portfolio_item(request, pk):
    _require_admin(request.user)
    item = get_object_or_404(EditorPortfolioItem, pk=pk)
    action = request.POST.get("action", "").strip()
    note = request.POST.get("review_note", "").strip()

    if action == "approve":
        item.review_status = EditorPortfolioItem.ReviewStatus.APPROVED
        item.is_active = True
        message = "نمونه‌کار تأیید و منتشر شد."
    elif action == "reject":
        item.review_status = EditorPortfolioItem.ReviewStatus.REJECTED
        item.is_active = False
        message = "نمونه‌کار رد شد."
    else:
        messages.error(request, "عملیات نامعتبر است.")
        return redirect("control_panel:portfolio_moderation")

    item.review_note = note
    item.reviewed_by = request.user
    item.reviewed_at = timezone.now()
    item.save()
    messages.success(request, message)
    return redirect("control_panel:portfolio_moderation")
