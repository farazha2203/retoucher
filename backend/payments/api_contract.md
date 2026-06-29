# Payment System API Contract
> نسخه ۲.۰ — مرجع کامل برای فرانت‌اند

---

## احراز هویت
همه endpoints نیاز به header دارند:
```
Authorization: Bearer <access_token>
```

---

## ۱. کیف‌پول کاربر

### موجودی من
```
GET /api/payments/wallet/me/
```
**Response:**
```json
{
  "id": 1,
  "user_username": "john",
  "user_email": "john@example.com",
  "user_role": "client",
  "user_full_name": "John Doe",
  "balance": "500000",
  "frozen_balance": "200000",
  "withdrawable_balance": "0",
  "available_balance": "300000",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

### تراکنش‌های من
```
GET /api/payments/wallet/me/transactions/
```
**Query params:** `tx_type`, `status`, `date_from`, `date_to`, `page`

**tx_type values:** `deposit`, `escrow_hold`, `escrow_release`, `payment`, `commission`, `editor_earning`, `withdrawal`, `refund`, `admin_adjustment`

**Response (paginated):**
```json
{
  "count": 50,
  "next": "?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "tx_type": "deposit",
      "tx_type_display": "شارژ کیف‌پول",
      "status": "success",
      "status_display": "موفق",
      "amount": "200000",
      "balance_before": "0",
      "balance_after": "200000",
      "order_id": null,
      "description": "شارژ از زرین‌پال",
      "created_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

### پرداخت‌های آنلاین من
```
GET /api/payments/wallet/me/payments/
GET /api/payments/wallet/me/payments/?status=success
```
**status values:** `created`, `redirected`, `success`, `failed`, `cancelled`

### جزئیات یک پرداخت
```
GET /api/payments/wallet/me/payments/{id}/
```

### صورت‌حساب من
```
GET /api/payments/wallet/me/invoice/?date_from=2025-01-01&date_to=2025-01-31
```
**Response:**
```json
{
  "invoice_number": "INV-1-20250115103000",
  "user_username": "john",
  "user_email": "john@example.com",
  "user_full_name": "John Doe",
  "generated_at": "2025-01-15T10:30:00Z",
  "period_from": "2025-01-01T00:00:00Z",
  "period_to": "2025-01-31T23:59:59Z",
  "transactions": [...],
  "payment_requests": [...],
  "total_deposited": "1000000",
  "total_spent": "500000",
  "total_earned": "0",
  "total_withdrawn": "0",
  "current_balance": "500000",
  "withdrawable_balance": "0"
}
```

---

## ۲. پرداخت آنلاین (زرین‌پال)

### شروع پرداخت
```
POST /api/payments/wallet/deposit/zarinpal/
```
**Body:**
```json
{
  "amount": 200000,
  "description": "شارژ کیف‌پول",
  "callback_url": "https://myapp.com/payment/callback",
  "order_id": null
}
```
**Response:**
```json
{
  "payment_url": "https://www.zarinpal.com/pg/StartPay/A0000...",
  "payment_request_id": 42
}
```
> فرانت باید کاربر را به `payment_url` redirect کند

### Callback (پس از بازگشت از درگاه)
```
GET /api/payments/wallet/deposit/zarinpal/callback/?Authority=A000...&Status=OK
```
**Response موفق:**
```json
{
  "success": true,
  "ref_id": "1234567890",
  "amount": "200000",
  "message": "پرداخت با موفقیت انجام شد."
}
```
**Response ناموفق:**
```json
{
  "success": false,
  "detail": "پرداخت توسط کاربر لغو شد."
}
```

### بررسی مجدد پرداخت pending
```
POST /api/payments/wallet/deposit/zarinpal/retry/{payment_request_id}/
```
**Response:**
```json
{
  "payment_url": "https://www.zarinpal.com/pg/StartPay/A000...",
  "payment_request_id": 42,
  "message": "لینک پرداخت مجدداً ارسال شد."
}
```

---

## ۳. برداشت (فقط ادیتور)

### ثبت درخواست برداشت
```
POST /api/payments/withdraw/request/
```
**Body:**
```json
{
  "amount": 500000,
  "bank_name": "بانک ملت",
  "card_number": "6104337812345678",
  "iban": "IR120570028080010957517001",
  "account_holder_name": "علی محمدی",
  "editor_note": "لطفاً تا فردا واریز کنید"
}
```

### لیست درخواست‌های خودم
```
GET /api/payments/withdraw/my-requests/
GET /api/payments/withdraw/my-requests/?status=pending
```
**status values:** `pending`, `approved`, `rejected`, `paid`

### جزئیات یک درخواست
```
GET /api/payments/withdraw/{id}/detail/
```

---

## ۴. پنل ادمین — Settlement

### داشبورد settlement
```
GET /api/payments/settlement/summary/
```
**Response:**
```json
{
  "pending": {
    "count": 5,
    "total_amount": 2500000,
    "older_than_3_days": 2
  },
  "paid": {
    "count": 120,
    "total_amount": 50000000
  },
  "settled": {
    "count": 120,
    "total_commission_earned": 5000000,
    "total_editor_paid": 45000000
  },
  "active_commission_percent": "10.00"
}
```

### لیست settlement_pending
```
GET /api/payments/settlement/pending/
GET /api/payments/settlement/pending/?search=john&min_amount=100000
```

### همه سفارش‌ها با فیلتر
```
GET /api/payments/settlement/all/?status=settlement_pending&payment_settled=false
```

### جزئیات یک سفارش
```
GET /api/payments/settlement/{order_id}/detail/
```
> شامل `preview_commission` و `preview_editor_earning` قبل از تسویه

### تنظیم مبلغ سفارش
```
POST /api/payments/settlement/{order_id}/set-price/
```
**Body:**
```json
{
  "agreed_price": 300000,
  "note": "توافق با مشتری"
}
```

### تسویه نهایی
```
POST /api/payments/settlement/{order_id}/settle/
```
**Body:**
```json
{
  "note": "تسویه تأیید شد"
}
```
**Response:**
```json
{
  "order": { ...order_detail... },
  "settlement": {
    "agreed_price": "300000",
    "commission": "30000",
    "editor_earning": "270000",
    "client_tx_id": 15,
    "editor_tx_id": 16
  }
}
```

---

## ۵. پنل ادمین — کیف‌پول و تراکنش

### داشبورد مالی
```
GET /api/payments/wallet/admin/summary/?date_from=2025-01-01&date_to=2025-01-31
```

### لیست همه کیف‌پول‌ها
```
GET /api/payments/wallet/admin/wallets/?search=john&role=editor
```

### کیف‌پول یک کاربر
```
GET /api/payments/wallet/admin/wallets/{user_id}/
```

### همه تراکنش‌ها
```
GET /api/payments/wallet/admin/transactions/?tx_type=commission&date_from=2025-01-01
```

### پرداخت‌های آنلاین
```
GET /api/payments/wallet/admin/payments/?status=failed&gateway=zarinpal
```

### پرداخت‌های در انتظار بررسی
```
GET /api/payments/wallet/admin/payments/pending/
```

### تفکیک وضعیت پرداخت‌ها
```
GET /api/payments/wallet/admin/status-breakdown/
```
**Response:**
```json
[
  {"status": "success", "gateway": "zarinpal", "count": 150, "total": 75000000},
  {"status": "failed", "gateway": "zarinpal", "count": 12, "total": 6000000},
  {"status": "cancelled", "gateway": "zarinpal", "count": 8, "total": 4000000}
]
```

### شارژ دستی کیف‌پول
```
POST /api/payments/wallet/admin/deposit/
```
**Body:**
```json
{
  "user_id": 5,
  "amount": 500000,
  "description": "هدیه ادمین"
}
```

### صورت‌حساب کاربر
```
GET /api/payments/wallet/admin/invoice/{user_id}/?date_from=2025-01-01
```

---

## ۶. پنل ادمین — مدیریت برداشت

### همه درخواست‌های برداشت
```
GET /api/payments/withdraw/admin/all/?status=pending
```

### درخواست‌های در انتظار
```
GET /api/payments/withdraw/admin/pending/
```

### تأیید برداشت
```
POST /api/payments/withdraw/{id}/approve/
```
**Body:** `{"admin_note": "تأیید شد"}`

### رد برداشت
```
POST /api/payments/withdraw/{id}/reject/
```
**Body:** `{"admin_note": "اطلاعات حساب نادرست است"}`

### علامت‌گذاری پرداخت‌شده
```
POST /api/payments/withdraw/{id}/mark-paid/
```

---

## ۷. تنظیمات کمیسیون

### کمیسیون فعال
```
GET /api/payments/wallet/admin/commission/
```

### تاریخچه تغییرات
```
GET /api/payments/wallet/admin/commission/history/
```

### تغییر نرخ کمیسیون
```
POST /api/payments/wallet/admin/commission/
```
**Body:**
```json
{
  "commission_percent": "12.00",
  "min_commission": "5000",
  "note": "افزایش به ۱۲٪ از فروردین ۱۴۰۴"
}
```

---

## کدهای خطا

| کد | معنا |
|---|---|
| 400 | خطای validation یا منطقی |
| 401 | احراز هویت نشده |
| 403 | دسترسی غیرمجاز |
| 404 | یافت نشد |
| 429 | درخواست بیش از حد (rate limit) |

**فرمت خطا:**
```json
{
  "detail": "پیام خطا"
}
```
یا:
```json
{
  "field_name": ["پیام خطای فیلد"]
}
```

---

## قوانین امنیتی

- ✅ هیچ تراکنشی قابل edit/delete نیست
- ✅ فقط ادمین می‌تواند تسویه انجام دهد
- ✅ فیش‌های تأیید‌شده (ref_id دار) قابل تغییر نیستند
- ✅ کاربر فقط تراکنش‌های خود را می‌بیند
- ✅ authority زرین‌پال در endpoint عمومی مخفی است
- ✅ Rate limit: ۱۰ درخواست/دقیقه برای پرداخت
- ✅ Double-verification: تأیید مجدد پرداخت‌های قبلاً موفق ممکن نیست
