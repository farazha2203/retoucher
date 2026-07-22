# فاز ۲.۱ فرانت — Foundation و Authentication

## خروجی

- Axios API Client مرکزی
- افزودن Bearer Token به درخواست‌ها
- Refresh خودکار Access Token
- جلوگیری از اجرای چند Refresh هم‌زمان
- پاک‌سازی Session در صورت نامعتبر شدن Refresh
- Zustand Auth Store با Persist
- دریافت اطلاعات کاربر از `/api/accounts/me/`
- Login واقعی با `username`
- Protected Route
- Dashboard اولیه و قابل اجرا

## مسیرهای API

```text
POST /api/auth/token/
POST /api/auth/token/refresh/
GET  /api/accounts/me/
```

## قواعد

- صفحه‌ها مستقیم Axios را صدا نمی‌زنند.
- تمام درخواست‌ها از `apiClient` عبور می‌کنند.
- Tokenها فقط از `useAuthStore` خوانده می‌شوند.
- در پاسخ 401 فقط یک Refresh هم‌زمان انجام می‌شود.
- بعد از شکست Refresh کاربر به Login برمی‌گردد.
