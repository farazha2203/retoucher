from decimal import Decimal

from django.db.models import Count

from accounts.models import EditorProfile


def calculate_editor_score(editor_profile):
    rating = Decimal(editor_profile.rating_average or 0)
    likes = editor_profile.portfolio_items.aggregate(total=Count("likes"))["total"] or 0
    completed = editor_profile.completed_orders_count or 0

    score = (
        rating * Decimal("6")
        + min(Decimal(likes), Decimal("500")) * Decimal("0.03")
        + min(Decimal(completed), Decimal("500")) * Decimal("0.02")
    )
    return score.quantize(Decimal("0.01"))


def editor_leaderboard(limit=50):
    rows = EditorProfile.objects.select_related("user").prefetch_related("portfolio_items")
    scored = []
    for row in rows:
        likes = row.portfolio_items.aggregate(total=Count("likes"))["total"] or 0
        scored.append(
            {
                "id": row.pk,
                "display_name": row.display_name or row.user.username,
                "rating": row.rating_average,
                "likes": likes,
                "completed_orders": row.completed_orders_count,
                "score": calculate_editor_score(row),
            }
        )
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]
