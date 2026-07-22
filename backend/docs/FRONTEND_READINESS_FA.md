# آمادگی فرانت‌اند — قرارداد API نسخه ۱

## هدف

این سند مرجع اتصال Frontend به Backend پروژه Retoucher است. از این مرحله به بعد، Frontend باید فقط به قراردادهای این سند و فایل `frontend_contract.v1.json` وابسته باشد.

## احراز هویت

### دریافت توکن

```http
POST /api/auth/token/
Content-Type: application/json
```

```json
{
  "username": "client01",
  "password": "ClientPass123!"
}
```

پاسخ:

```json
{
  "refresh": "JWT_REFRESH_TOKEN",
  "access": "JWT_ACCESS_TOKEN"
}
```

### تمدید توکن

```http
POST /api/auth/token/refresh/
```

```json
{
  "refresh": "JWT_REFRESH_TOKEN"
}
```

### هدر درخواست‌های خصوصی

```http
Authorization: Bearer JWT_ACCESS_TOKEN
```

در Swagger فقط خود توکن وارد می‌شود؛ کلمه `Bearer` را Swagger اضافه می‌کند.

## Endpointهای تثبیت‌شده برای Workflow

```text
GET /api/orders/
GET /api/orders/{id}/
GET /api/orders/{id}/timeline/

GET /api/projects/requests/
GET /api/projects/requests/{id}/
GET /api/projects/requests/{id}/timeline/
```

## قرارداد Workflow

```json
{
  "workflow_type": "order",
  "status": "in_progress",
  "stage": {
    "key": "editing",
    "title_fa": "در حال ادیت",
    "title_en": "Editing"
  },
  "progress_percent": 45,
  "terminal": false,
  "successful": false,
  "waiting_for_role": "editor",
  "next_action": "upload_delivery",
  "deadline": {
    "at": "2026-07-25T12:00:00Z",
    "state": "active",
    "is_overdue": false,
    "stage": "editing",
    "owner_role": "editor",
    "timeout_action": "notify"
  }
}
```

## قواعد Frontend

- درصد پیشرفت را Frontend محاسبه نمی‌کند.
- Deadline و overdue را Backend تعیین می‌کند.
- Frontend بر اساس `next_action` دکمه مناسب را نمایش می‌دهد.
- `waiting_for_role` مشخص می‌کند سفارش منتظر چه نقشی است.
- تاریخچه فقط از endpoint `timeline` خوانده می‌شود.
- داده خصوصی با پاسخ 401/403/404 باید بدون نمایش جزئیات مدیریت شود.
- برای تاریخ‌ها از ISO-8601 دریافتی Backend استفاده و در رابط به تاریخ شمسی تبدیل شود.

## وضعیت‌های HTTP

| کد | رفتار فرانت |
|---:|---|
| 200 | نمایش داده |
| 400 | نمایش خطای اعتبارسنجی |
| 401 | پاک‌کردن access و تلاش برای refresh |
| 403 | نمایش عدم دسترسی |
| 404 | نمایش «یافت نشد» بدون افشای مالک |
| 409 | نمایش تعارض وضعیت Workflow |
| 500 | نمایش خطای عمومی و request-id در آینده |

## راهبرد Token

- Access token فقط در حافظه یا storage امن نگهداری شود.
- Refresh token ترجیحاً با HttpOnly Cookie پیاده شود؛ در فاز اول می‌تواند موقتاً در storage باشد.
- در پاسخ 401 ابتدا یک‌بار refresh انجام شود.
- اگر refresh شکست خورد، کاربر به صفحه ورود برگردد.

## Gate شروع Frontend

Backend برای شروع Frontend آماده است وقتی:

- JWT integration test سبز باشد.
- Timeline owner با 200 پاسخ دهد.
- anonymous با 401 رد شود.
- outsider با 403 یا 404 رد شود.
- `workflow`, `progress_percent`, `deadline`, `next_action` در جزئیات وجود داشته باشند.
- OpenAPI schema بدون خطا export شود.
