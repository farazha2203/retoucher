# قرارداد گردش‌کار برای فرانت‌اند

این سند قرارداد خواندن وضعیت، درصد پیشرفت، ددلاین و Timeline را برای فرانت‌اند توضیح می‌دهد.

## اصل معماری

- فرانت‌اند وضعیت را تغییر نمی‌دهد؛ فقط Action API مناسب را فراخوانی می‌کند.
- فیلد `workflow` منبع نمایش Progress Bar، مرحله فعلی، مسئول اقدام بعدی و ددلاین است.
- Timeline برای نمایش تاریخچه شفاف سفارش یا درخواست استفاده می‌شود.
- مقدار `progress_percent` از وضعیت جاری محاسبه می‌شود و در این فاز در دیتابیس ذخیره نمی‌شود.

## خلاصه Workflow

در پاسخ لیست و جزئیات Order و ProjectRequest، فیلد زیر افزوده می‌شود:

```json
{
  "workflow": {
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
      "at": "2026-07-25T14:00:00+00:00",
      "state": "active",
      "is_overdue": false
    }
  }
}
```

## Endpointهای Timeline

```text
GET /api/orders/{id}/timeline/
GET /api/projects/requests/{id}/timeline/
```

خروجی:

```json
{
  "workflow": {},
  "events": [
    {
      "event_id": "order-status-15",
      "event_key": "status_changed",
      "entity_type": "order",
      "entity_id": 8,
      "source": "status_history",
      "actor": {"id": 3, "username": "admin"},
      "from_status": "completed",
      "to_status": "settlement_pending",
      "message": "Settlement started.",
      "metadata": {},
      "occurred_at": "2026-07-21T10:30:00+00:00"
    }
  ]
}
```

## راهنمای رابط کاربری

- `stage.title_fa`: عنوان اصلی مرحله
- `progress_percent`: مقدار Progress Bar
- `deadline.state=overdue`: نمایش هشدار قرمز
- `waiting_for_role`: تعیین اینکه CTA برای چه نقشی نمایش داده شود
- `next_action`: کلید تصمیم‌گیری برای متن یا دکمه بعدی
- `terminal=true`: مخفی‌کردن CTAهای اجرایی
- `successful=false` همراه terminal: پایان ناموفق مانند لغو یا انقضا

## سازگاری

تمام فیلدها افزایشی هستند. Endpointها و فیلدهای قبلی حذف یا تغییر نام داده نشده‌اند.
