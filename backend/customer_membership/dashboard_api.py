from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .ranking import editor_leaderboard
from .studio_ads import active_studio_ads


class EditorLeaderboardView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return Response(editor_leaderboard())


class StudioDirectoryView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        rows = active_studio_ads().order_by("-featured_until", "studio_name")
        return Response(
            [
                {
                    "id": row.pk,
                    "studio_name": row.studio_name,
                    "city": row.city,
                    "activity_fields": row.activity_fields,
                    "logo": row.logo.url if row.logo else None,
                    "website": row.website,
                    "instagram": row.instagram,
                    "description": row.description,
                    "featured": bool(row.featured_until),
                }
                for row in rows
            ]
        )
