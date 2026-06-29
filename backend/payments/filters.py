import django_filters
from django.db.models import Q

from .models import PaymentRequest, Transaction, Wallet, WithdrawRequest


class TransactionFilter(django_filters.FilterSet):
    tx_type = django_filters.CharFilter(field_name="tx_type")
    status = django_filters.CharFilter(field_name="status")
    date_from = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    date_to = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    amount_min = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")
    order_id = django_filters.NumberFilter(field_name="order__id")
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Transaction
        fields = ["tx_type", "status", "order_id"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(description__icontains=value) |
            Q(wallet__user__username__icontains=value) |
            Q(wallet__user__email__icontains=value)
        )


class PaymentRequestFilter(django_filters.FilterSet):
    gateway = django_filters.CharFilter(field_name="gateway")
    status = django_filters.CharFilter(field_name="status")
    date_from = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    date_to = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    amount_min = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = PaymentRequest
        fields = ["gateway", "status"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(user__username__icontains=value) |
            Q(user__email__icontains=value) |
            Q(ref_id__icontains=value) |
            Q(authority__icontains=value)
        )


class WithdrawRequestFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status")
    date_from = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    date_to = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    amount_min = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = WithdrawRequest
        fields = ["status"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(editor__username__icontains=value) |
            Q(editor__email__icontains=value) |
            Q(card_number__icontains=value) |
            Q(iban__icontains=value)
        )


class WalletFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    balance_min = django_filters.NumberFilter(field_name="balance", lookup_expr="gte")
    balance_max = django_filters.NumberFilter(field_name="balance", lookup_expr="lte")
    role = django_filters.CharFilter(field_name="user__role")

    class Meta:
        model = Wallet
        fields = []

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(user__username__icontains=value) |
            Q(user__email__icontains=value) |
            Q(user__first_name__icontains=value) |
            Q(user__last_name__icontains=value)
        )
