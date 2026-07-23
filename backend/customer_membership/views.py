from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CustomerProfile, CustomerTier
from .serializers import CustomerProfileSerializer, CustomerTierSerializer


class CustomerProfileMeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, user):
        default_tier = CustomerTier.objects.filter(code=CustomerTier.Code.NORMAL, is_active=True).first()
        profile, _ = CustomerProfile.objects.get_or_create(user=user, defaults={"tier": default_tier})
        return profile

    def get(self, request):
        return Response(CustomerProfileSerializer(self.get_object(request.user), context={"request": request}).data)

    def patch(self, request):
        serializer = CustomerProfileSerializer(self.get_object(request.user), data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CustomerTierListView(APIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request):
        return Response(CustomerTierSerializer(CustomerTier.objects.filter(is_active=True), many=True).data)
