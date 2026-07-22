# فاز ۲.۲ فرانت — داشبورد Workflow

## امکانات

- Dashboard Layout واکنش‌گرا
- Sidebar
- مسیرهای Orders و Project Requests
- اتصال واقعی به Backend
- نمایش درصد پیشرفت
- نمایش Deadline و overdue
- نمایش نقش منتظر
- Timeline Drawer
- پشتیبانی از پاسخ لیستی و Paginated DRF

## Endpointها

```text
GET /api/orders/
GET /api/orders/{id}/timeline/
GET /api/projects/requests/
GET /api/projects/requests/{id}/timeline/
```

## مسیرهای فرانت

```text
/dashboard
/dashboard/orders
/dashboard/projects
/dashboard/wallet
/dashboard/notifications
/dashboard/settings
```
