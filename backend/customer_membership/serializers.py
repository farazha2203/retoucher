from rest_framework import serializers
from .models import CustomerProfile, CustomerSubscription, CustomerTier, StudioProfile


class CustomerTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerTier
        fields = "__all__"


class StudioProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudioProfile
        exclude = ("customer", "created_at", "updated_at")
        read_only_fields = ("is_verified", "advertising_enabled")


class CustomerProfileSerializer(serializers.ModelSerializer):
    tier = CustomerTierSerializer(read_only=True)
    studio = StudioProfileSerializer(required=False, allow_null=True)
    effective_discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    effective_priority_level = serializers.IntegerField(read_only=True)

    class Meta:
        model = CustomerProfile
        exclude = ("user", "admin_note", "created_at", "updated_at")
        read_only_fields = ("profile_completed",)

    def update(self, instance, validated_data):
        studio_data = validated_data.pop("studio", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.profile_completed = all([instance.national_id, instance.landline, instance.occupation, instance.city, instance.address])
        instance.save()
        if studio_data is not None:
            studio, _ = StudioProfile.objects.get_or_create(customer=instance, defaults={"studio_name": studio_data.get("studio_name", "")})
            for field, value in studio_data.items():
                setattr(studio, field, value)
            studio.save()
        return instance


class CustomerSubscriptionSerializer(serializers.ModelSerializer):
    tier = CustomerTierSerializer(read_only=True)
    class Meta:
        model = CustomerSubscription
        fields = "__all__"
