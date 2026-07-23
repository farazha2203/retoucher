from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import PortfolioComment, PortfolioCommentReport, PortfolioLike


def _require_admin(user):
    if not (user.is_superuser or user.is_staff or getattr(user, "role", "") == "admin"):
        raise PermissionDenied


@login_required
def social_moderation(request):
    _require_admin(request.user)

    state = request.GET.get("state", "pending").strip()
    query = request.GET.get("q", "").strip()

    comments = (
        PortfolioComment.objects.select_related(
            "user", "portfolio_item", "portfolio_item__editor"
        )
        .annotate(report_count=Count("reports", distinct=True))
        .order_by("-created_at")
    )

    if state in {
        PortfolioComment.Status.PENDING,
        PortfolioComment.Status.APPROVED,
        PortfolioComment.Status.HIDDEN,
    }:
        comments = comments.filter(status=state)

    if query:
        comments = comments.filter(
            Q(body__icontains=query)
            | Q(user__username__icontains=query)
            | Q(portfolio_item__title__icontains=query)
            | Q(portfolio_item__editor__display_name__icontains=query)
        )

    reports = (
        PortfolioCommentReport.objects.select_related(
            "comment",
            "comment__user",
            "comment__portfolio_item",
            "reporter",
        )
        .order_by("-created_at")[:100]
    )

    return render(
        request,
        "control_panel/social_moderation.html",
        {
            "page_title": "مدیریت لایک و دیدگاه نمونه‌کارها",
            "comments": comments[:300],
            "reports": reports,
            "selected_state": state,
            "query": query,
            "pending_count": PortfolioComment.objects.filter(
                status=PortfolioComment.Status.PENDING
            ).count(),
            "approved_count": PortfolioComment.objects.filter(
                status=PortfolioComment.Status.APPROVED
            ).count(),
            "hidden_count": PortfolioComment.objects.filter(
                status=PortfolioComment.Status.HIDDEN
            ).count(),
            "open_reports_count": PortfolioCommentReport.objects.filter(
                status=PortfolioCommentReport.Status.OPEN
            ).count(),
            "likes_count": PortfolioLike.objects.count(),
        },
    )


@login_required
@require_POST
def moderate_portfolio_comment(request, pk):
    _require_admin(request.user)
    comment = get_object_or_404(PortfolioComment, pk=pk)
    action = request.POST.get("action", "").strip()

    if action == "approve":
        comment.status = PortfolioComment.Status.APPROVED
        message = "دیدگاه تأیید شد."
    elif action == "hide":
        comment.status = PortfolioComment.Status.HIDDEN
        message = "دیدگاه مخفی شد."
    else:
        messages.error(request, "عملیات نامعتبر است.")
        return redirect("control_panel:social_moderation")

    comment.moderated_by = request.user
    comment.moderated_at = timezone.now()
    comment.save(
        update_fields=("status", "moderated_by", "moderated_at", "updated_at")
    )
    messages.success(request, message)
    return redirect(request.POST.get("next") or "control_panel:social_moderation")


@login_required
@require_POST
def moderate_portfolio_report(request, pk):
    _require_admin(request.user)
    report = get_object_or_404(PortfolioCommentReport, pk=pk)
    action = request.POST.get("action", "").strip()

    if action == "review":
        report.status = PortfolioCommentReport.Status.REVIEWED
        message = "گزارش بررسی‌شده ثبت شد."
    elif action == "dismiss":
        report.status = PortfolioCommentReport.Status.DISMISSED
        message = "گزارش رد شد."
    else:
        messages.error(request, "عملیات گزارش نامعتبر است.")
        return redirect("control_panel:social_moderation")

    report.save(update_fields=("status",))
    messages.success(request, message)
    return redirect("control_panel:social_moderation")
