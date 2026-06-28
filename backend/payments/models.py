from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class Wallet(models.Model):
    """
    هر کاربر یک کیف‌پول دارد.
    balance: موجودی کل
    frozen_balance: مبالغ در حال escrow (بلوکه شده برای سفارش‌های در جریان)
    withdrawable_balance: موجودی قابل برداشت (برای ادیتورها)
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet",
    )
    balance = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    frozen_balance = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    withdrawable_balance = models.DecimalField(max_digits=14, decimal_places=0, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"

    def __str__(self):
        return f"Wallet({self.user.username}) balance={self.balance}"

    @property
    def available_balance(self):
        """موجودی در دسترس برای مشتری (بدون مبالغ بلوکه‌شده)"""
        return self.balance - self.frozen_balance

    def can_afford(self, amount: Decimal) -> bool:
        return self.available_balance >= amount

    def freeze(self, amount: Decimal):
        """مبلغ رو برای یک سفارش بلوکه کن (escrow)"""
        if not self.can_afford(amount):
            raise ValidationError("موجودی کافی نیست.")
        self.frozen_balance += amount
        self.save(update_fields=["frozen_balance", "updated_at"])

    def unfreeze(self, amount: Decimal):
        """آزاد کردن مبلغ بلوکه‌شده (لغو سفارش)"""
        self.frozen_balance = max(Decimal(0), self.frozen_balance - amount)
        self.save(update_fields=["frozen_balance", "updated_at"])

    def deduct_frozen(self, amount: Decimal):
        """کم کردن از موجودی و frozen با هم (تأیید پرداخت)"""
        self.balance -= amount
        self.frozen_balance = max(Decimal(0), self.frozen_balance - amount)
        self.save(update_fields=["balance", "frozen_balance", "updated_at"])

    def credit(self, amount: Decimal):
        """افزودن به موجودی (شارژ کیف‌پول یا دریافت از سفارش)"""
        self.balance += amount
        self.save(update_fields=["balance", "updated_at"])

    def credit_withdrawable(self, amount: Decimal):
        """افزودن به موجودی قابل برداشت ادیتور"""
        self.balance += amount
        self.withdrawable_balance += amount
        self.save(update_fields=["balance", "withdrawable_balance", "updated_at"])

    def deduct_withdrawable(self, amount: Decimal):
        """کم کردن از موجودی قابل برداشت (هنگام برداشت)"""
        if self.withdrawable_balance < amount:
            raise ValidationError("موجودی قابل برداشت کافی نیست.")
        self.balance -= amount
        self.withdrawable_balance -= amount
        self.save(update_fields=["balance", "withdrawable_balance", "updated_at"])


class Transaction(models.Model):
    """
    هر تراکنش مالی در سیستم — immutable log
    """

    class TxType(models.TextChoices):
        DEPOSIT = "deposit", "شارژ کیف‌پول"
        ESCROW_HOLD = "escrow_hold", "بلوکه برای سفارش"
        ESCROW_RELEASE = "escrow_release", "آزاد از escrow (لغو)"
        PAYMENT = "payment", "پرداخت سفارش"
        COMMISSION = "commission", "کمیسیون سایت"
        EDITOR_EARNING = "editor_earning", "درآمد ادیتور"
        WITHDRAWAL = "withdrawal", "برداشت ادیتور"
        REFUND = "refund", "استرداد وجه"
        ADMIN_ADJUSTMENT = "admin_adjustment", "تعدیل ادمین"

    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار"
        SUCCESS = "success", "موفق"
        FAILED = "failed", "ناموفق"
        REVERSED = "reversed", "برگشت خورده"

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    tx_type = models.CharField(max_length=30, choices=TxType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    amount = models.DecimalField(max_digits=14, decimal_places=0)
    balance_before = models.DecimalField(max_digits=14, decimal_places=0)
    balance_after = models.DecimalField(max_digits=14, decimal_places=0)

    # ارتباط با سفارش (اختیاری)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    # ارتباط با پرداخت آنلاین (اختیاری)
    payment_request = models.ForeignKey(
        "PaymentRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    description = models.CharField(max_length=255, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_transactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return f"TX[{self.tx_type}] {self.amount} → {self.wallet.user.username}"


class PaymentRequest(models.Model):
    """
    درخواست پرداخت آنلاین (زرین‌پال و درگاه‌های آینده)
    """

    class Gateway(models.TextChoices):
        ZARINPAL = "zarinpal", "زرین‌پال"
        MANUAL = "manual", "دستی (ادمین)"

    class Status(models.TextChoices):
        CREATED = "created", "ایجاد شده"
        REDIRECTED = "redirected", "هدایت به درگاه"
        SUCCESS = "success", "پرداخت موفق"
        FAILED = "failed", "پرداخت ناموفق"
        CANCELLED = "cancelled", "لغو شده"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_requests",
    )
    gateway = models.CharField(max_length=20, choices=Gateway.choices, default=Gateway.ZARINPAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)

    amount = models.DecimalField(max_digits=14, decimal_places=0)  # تومان
    description = models.CharField(max_length=255, blank=True)

    # زرین‌پال
    authority = models.CharField(max_length=100, blank=True, db_index=True)
    ref_id = models.CharField(max_length=100, blank=True)  # شماره پیگیری نهایی
    gateway_response = models.JSONField(default=dict, blank=True)

    # برای شارژ کیف‌پول یا پرداخت مستقیم سفارش
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_requests",
    )

    callback_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Payment Request"
        verbose_name_plural = "Payment Requests"

    def __str__(self):
        return f"Pay[{self.gateway}] {self.amount} - {self.user.username} ({self.status})"


class WithdrawRequest(models.Model):
    """
    درخواست برداشت ادیتور
    """

    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار بررسی"
        APPROVED = "approved", "تأیید شده"
        REJECTED = "rejected", "رد شده"
        PAID = "paid", "پرداخت شده"

    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="withdraw_requests",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # اطلاعات حساب بانکی
    bank_name = models.CharField(max_length=100, blank=True)
    card_number = models.CharField(max_length=20, blank=True)
    iban = models.CharField(max_length=30, blank=True)
    account_holder_name = models.CharField(max_length=150, blank=True)

    editor_note = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_withdraw_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Withdraw Request"
        verbose_name_plural = "Withdraw Requests"

    def __str__(self):
        return f"Withdraw {self.amount} by {self.editor.username} ({self.status})"


class SiteCommissionSetting(models.Model):
    """
    تنظیمات کمیسیون سایت — ادمین می‌تواند تغییر دهد
    فقط یک رکورد active در هر لحظه داریم
    """

    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("10.00"),
        help_text="درصد کمیسیون سایت از هر سفارش (مثلاً 10.00 = ۱۰٪)",
    )
    min_commission = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=Decimal("0"),
        help_text="حداقل مبلغ کمیسیون (تومان)",
    )
    is_active = models.BooleanField(default=True)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Commission Setting"
        verbose_name_plural = "Commission Settings"

    def __str__(self):
        return f"Commission {self.commission_percent}% (active={self.is_active})"

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).order_by("-created_at").first()

    def calculate(self, amount: Decimal) -> tuple[Decimal, Decimal]:
        """
        Returns (commission_amount, editor_earning)
        """
        commission = (amount * self.commission_percent / Decimal("100")).quantize(Decimal("1"))
        commission = max(commission, self.min_commission)
        commission = min(commission, amount)
        editor_earning = amount - commission
        return commission, editor_earning
