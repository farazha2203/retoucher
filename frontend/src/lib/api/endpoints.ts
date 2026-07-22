// این فایل مسیرهای API را یک‌جا نگه می‌دارد
// TODO: بعد از دریافت accounts/urls.py، payments/urls.py و ... مقادیر دقیق جایگزین می‌شوند

export const API_ENDPOINTS = {
  auth: {
    register: "/auth/register/",
    login: "/auth/login/",
    refresh: "/auth/refresh/",
    me: "/me/",
  },
  catalog: {
    categories: "/catalog/categories/",
  },
  projects: {
    list: "/projects/",
    detail: (id: number | string) => `/projects/${id}/`,
    proposals: (id: number | string) => `/projects/${id}/proposals/`,
  },
  orders: {
    list: "/orders/",
    detail: (id: number | string) => `/orders/${id}/`,
    deliveries: (id: number | string) => `/orders/${id}/deliveries/`,
  },
  payments: {
    start: "/payments/start/",
    verify: "/payments/verify/",
    wallet: "/payments/wallet/",
  },
} as const;