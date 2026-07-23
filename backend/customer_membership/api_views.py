from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .billing import MembershipBillingError, purchase_membership
from .models import CustomerTier
from .serializers import CustomerSubscriptionSerializer


class PurchaseMembershipView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        tier_id = request.data.get("tier_id")
        period = str(request.data.get("period") or "").strip()

        tier = CustomerTier.objects.filter(pk=tier_id).first()
        if tier is None:
            return Response(
                {"tier_id": ["پلن پیدا نشد."]},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            subscription = purchase_membership(
                user=request.user,
                tier=tier,
                period=period,
            )
        except MembershipBillingError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            CustomerSubscriptionSerializer(subscription).data,
            status=status.HTTP_201_CREATED,
        )
