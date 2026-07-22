

# src\lib\api\client.ts

```tsx
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// Attach access token
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('retoucher-auth');
    if (stored) {
      try {
        const { state } = JSON.parse(stored);
        if (state?.accessToken) {
          config.headers.Authorization = `Bearer ${state.accessToken}`;
        }
      } catch {}
    }
  }
  return config;
});

// Refresh token on 401
let isRefreshing = false;
let queue: Array<{ resolve: (v: string) => void; reject: (e: unknown) => void }> = [];

apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true;

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          queue.push({
            resolve: (token) => {
              original.headers.Authorization = `Bearer ${token}`;
              resolve(apiClient(original));
            },
            reject,
          });
        });
      }

      isRefreshing = true;

      try {
        const stored = localStorage.getItem('retoucher-auth');
        const { state } = JSON.parse(stored || '{}');
        const refreshToken = state?.refreshToken;

        if (!refreshToken) throw new Error('No refresh token');

        const { data } = await axios.post(`${API_URL}/api/auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const parsed = JSON.parse(localStorage.getItem('retoucher-auth') || '{}');
        if (!parsed.state) parsed.state = {};
        parsed.state.accessToken = data.access;
        if (data.refresh) parsed.state.refreshToken = data.refresh;
        localStorage.setItem('retoucher-auth', JSON.stringify(parsed));

        queue.forEach((q) => q.resolve(data.access));
        queue = [];

        original.headers.Authorization = `Bearer ${data.access}`;
        return apiClient(original);
      } catch {
        queue.forEach((q) => q.reject(error));
        queue = [];
        localStorage.removeItem('retoucher-auth');
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
```


# src\lib\api\auth.ts

```tsx
import { apiClient } from './client';
import type { User } from '@/types';

export type BackendUserRole = 'client' | 'editor';
export type UiUserRole = 'client' | 'editor' | 'studio' | 'atelier';

// برای سازگاری با register page فعلی
export type UserRole = UiUserRole;

export type AuthUser = User & {
  is_staff?: boolean;
  is_superuser?: boolean;
};

export type LoginPayload = {
  username?: string;
  email?: string;
  password: string;
};

export type RegisterPayload = {
  username: string;
  email: string;
  password: string;

  password2?: string;
  password_confirm?: string;

  first_name?: string;
  last_name?: string;

  role: UiUserRole;

  phone?: string;
  city?: string;
  bio?: string;
  portfolio_url?: string;
  instagram?: string;
  website?: string;
  studio_name?: string;
};

export type AuthResponse = {
  access?: string;
  refresh?: string;
  access_token?: string;
  refresh_token?: string;
  token?: string;
  user?: AuthUser;
  detail?: string;
  message?: string;
};

function getAccessToken(data: AuthResponse): string | null {
  return data.access || data.access_token || data.token || null;
}

function getRefreshToken(data: AuthResponse): string | null {
  return data.refresh || data.refresh_token || null;
}

function normalizeBackendRole(role: UiUserRole): BackendUserRole {
  if (role === 'editor') return 'editor';

  // backend فعلاً فقط client/editor دارد
  // studio/atelier فعلاً به عنوان client ثبت می‌شود
  return 'client';
}

export function hasTokenResponse(data: AuthResponse): boolean {
  return Boolean(
    data.access ||
      data.access_token ||
      data.token ||
      data.refresh ||
      data.refresh_token
  );
}

export function saveAuthSession(data: AuthResponse) {
  if (typeof window === 'undefined') return;

  const accessToken = getAccessToken(data);
  const refreshToken = getRefreshToken(data);

  const currentRaw = localStorage.getItem('retoucher-auth');

  let parsed: {
    state?: {
      accessToken?: string | null;
      refreshToken?: string | null;
      user?: AuthUser | null;
    };
    version?: number;
  } = {};

  if (currentRaw) {
    try {
      parsed = JSON.parse(currentRaw);
    } catch {
      parsed = {};
    }
  }

  if (!parsed.state) parsed.state = {};

  if (accessToken) parsed.state.accessToken = accessToken;
  if (refreshToken) parsed.state.refreshToken = refreshToken;
  if (data.user) parsed.state.user = data.user;

  localStorage.setItem('retoucher-auth', JSON.stringify(parsed));

  // fallback برای بخش‌های احتمالی دیگر پروژه
  if (accessToken) {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('access', accessToken);
  }

  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('refreshToken', refreshToken);
    localStorage.setItem('refresh', refreshToken);
  }

  if (data.user) {
    localStorage.setItem('user', JSON.stringify(data.user));
  }
}

export function clearAuthSession() {
  if (typeof window === 'undefined') return;

  localStorage.removeItem('retoucher-auth');

  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('access');
  localStorage.removeItem('refresh');
  localStorage.removeItem('user');
}

export function getStoredAccessToken(): string | null {
  if (typeof window === 'undefined') return null;

  const stored = localStorage.getItem('retoucher-auth');

  if (stored) {
    try {
      const { state } = JSON.parse(stored);
      if (state?.accessToken) return state.accessToken;
    } catch {
      // ignore
    }
  }

  return (
    localStorage.getItem('access_token') ||
    localStorage.getItem('accessToken') ||
    localStorage.getItem('access')
  );
}

export const authAPI = {
  register: async (payload: RegisterPayload): Promise<AuthResponse> => {
    const backendRole = normalizeBackendRole(payload.role);

    const body = {
      username: payload.username,
      email: payload.email,
      password: payload.password,
      password2: payload.password2 || payload.password_confirm || payload.password,
      password_confirm: payload.password_confirm || payload.password2 || payload.password,
      first_name: payload.first_name || '',
      last_name: payload.last_name || '',
      role: backendRole,
    };

    const { data } = await apiClient.post('/api/accounts/register/', body);

    if (hasTokenResponse(data)) {
      saveAuthSession(data);
    }

    return data;
  },

  login: async (payload: LoginPayload): Promise<AuthResponse> => {
    const usernameOrEmail = payload.username || payload.email || '';

    const body = {
      username: usernameOrEmail,
      email: usernameOrEmail,
      password: payload.password,
    };

    // endpoint واقعی backend
    const { data } = await apiClient.post('/api/auth/token/', body);

    // خیلی مهم: قبل از getMe باید token ذخیره شود
    saveAuthSession(data);

    return data;
  },

  me: async (): Promise<AuthUser> => {
    const { data } = await apiClient.get('/api/accounts/me/');
    return data;
  },

  getMe: async (): Promise<AuthUser> => {
    const { data } = await apiClient.get('/api/accounts/me/');
    return data;
  },

  logout: async (): Promise<void> => {
    clearAuthSession();
  },

  forgotPassword: async (email: string): Promise<unknown> => {
    const { data } = await apiClient.post('/api/accounts/forgot-password/', { email });
    return data;
  },

  verifyOTP: async (email: string, code: string): Promise<unknown> => {
    const { data } = await apiClient.post('/api/accounts/verify-otp/', {
      email,
      code,
      otp: code,
    });
    return data;
  },

  resetPassword: async (
    payloadOrToken:
      | string
      | {
          token?: string;
          code?: string;
          otp?: string;
          uid?: string;
          uidb64?: string;
          email?: string;
          password?: string;
          new_password?: string;
          password2?: string;
          new_password2?: string;
        },
    newPassword?: string
  ): Promise<unknown> => {
    if (typeof payloadOrToken === 'string') {
      const token = payloadOrToken;

      const { data } = await apiClient.post('/api/accounts/reset-password/', {
        token,
        code: token,
        otp: token,
        password: newPassword,
        password2: newPassword,
        new_password: newPassword,
        new_password2: newPassword,
      });

      return data;
    }

    const { data } = await apiClient.post('/api/accounts/reset-password/', payloadOrToken);
    return data;
  },

  saveSession: saveAuthSession,
  clearSession: clearAuthSession,
};
```


# src\app\(auth)\login\page.tsx

```tsx
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { authAPI } from '../../../lib/api/auth';
import { useAuthStore } from '../../../lib/stores/auth.store';

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();

  const [form, setForm] = useState({ email: '', password: '' });
  const [showPass, setShowPass] = useState(false);
  const [remember, setRemember] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isValid = form.email.includes('@') && form.password.length >= 6;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;
    setLoading(true);
    setError('');
    try {
      const data = await authAPI.login({ email: form.email, password: form.password });
      const me = await authAPI.getMe();
      setAuth(me, data.access, data.refresh);
      router.push('/dashboard');
    } catch {
      setError('ایمیل یا رمز عبور اشتباه است.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left Art Panel */}
      <div
        className="hidden lg:flex flex-1 flex-col items-center justify-center p-12 relative overflow-hidden"
        style={{ background: 'linear-gradient(145deg,#FDF0F6 0%,#F3F0FE 40%,#EEF8F4 100%)' }}
      >
        <div
          className="absolute -top-20 -right-20 w-72 h-72 rounded-full"
          style={{ background: 'rgba(196,181,244,.2)' }}
        />
        <div
          className="absolute -bottom-16 -left-16 w-56 h-56 rounded-full"
          style={{ background: 'rgba(168,213,194,.2)' }}
        />
        <div className="relative z-10 text-center">
          <div className="text-4xl font-semibold text-gray-800 leading-snug">
            خلاقیت را<br />
            <span style={{ color: '#E07AA0' }}>حرفه‌ای</span> بفروش
          </div>
          <p className="mt-4 text-gray-500 text-sm leading-relaxed max-w-xs mx-auto">
            مارکت‌پلیس تخصصی روتوش، ادیت عکس و هوش مصنوعی تصویری
          </p>
          <div className="flex flex-wrap gap-2 mt-8 justify-center">
            {[
              { label: 'روتوش حرفه‌ای', bg: '#FDF0F6', color: '#E07AA0' },
              { label: 'ادیت عکس', bg: '#F3F0FE', color: '#9B85E8' },
              { label: 'هوش مصنوعی', bg: '#EEF8F4', color: '#6DB89A' },
              { label: 'آتلیه', bg: '#FEF5F0', color: '#E89B6D' },
            ].map((b) => (
              <span
                key={b.label}
                className="px-4 py-1.5 rounded-full text-sm font-medium"
                style={{ background: b.bg, color: b.color }}
              >
                {b.label}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Right Form Panel */}
      <div
        className="flex-1 lg:max-w-md flex items-center justify-center px-8 py-12"
        style={{ background: 'white' }}
      >
        <form onSubmit={handleSubmit} className="w-full max-w-sm">
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-6">
              <div
                className="w-8 h-8 rounded-xl flex items-center justify-center text-base"
                style={{ background: 'linear-gradient(135deg,#F2A8C4,#C4B5F4)' }}
              >
                ✦
              </div>
              <span className="font-semibold text-lg text-gray-800">ریتاچر</span>
            </div>
            <h1 className="text-2xl font-semibold text-gray-800">خوش برگشتی 👋</h1>
            <p className="mt-2 text-sm" style={{ color: '#7B7B90' }}>
              حساب ندارید؟{' '}
              <Link href="/register" style={{ color: '#9B85E8' }} className="font-medium">
                ثبت‌نام کنید
              </Link>
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">ایمیل</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                placeholder="name@example.com"
                className="input-auth w-full px-4 py-3 rounded-xl text-sm bg-gray-50 outline-none"
                style={{ fontFamily: 'inherit' }}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">رمز عبور</label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  value={form.password}
                  onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                  placeholder="حداقل ۸ کاراکتر"
                  className="input-auth w-full px-4 py-3 rounded-xl text-sm bg-gray-50 outline-none pr-10"
                  style={{ fontFamily: 'inherit' }}
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                >
                  {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between mt-4 mb-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm" style={{ color: '#7B7B90' }}>مرا به خاطر بسپار</span>
            </label>
            <Link href="/forgot-password" className="text-sm font-medium" style={{ color: '#9B85E8' }}>
              فراموش کردید؟
            </Link>
          </div>

          {error && (
            <div
              className="mb-4 p-3 rounded-xl text-sm"
              style={{ background: '#FEF5F0', color: '#E89B6D', border: '1px solid rgba(232,155,109,.3)' }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={!isValid || loading}
            className="btn-auth-primary w-full py-3 rounded-xl text-white font-semibold text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : null}
            {loading ? 'در حال ورود...' : 'ورود به حساب'}
          </button>

          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-gray-100" />
            <span className="text-xs text-gray-400">یا</span>
            <div className="flex-1 h-px bg-gray-100" />
          </div>

          <div className="flex gap-3">
            {[
              { icon: '🔵', label: 'Google' },
              { icon: '⚫', label: 'Apple' },
            ].map((s) => (
              <button
                key={s.label}
                type="button"
                className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium border transition-colors hover:bg-gray-50"
                style={{ borderColor: '#EBEBF0', color: '#2D2D3A', fontFamily: 'inherit' }}
              >
                <span>{s.icon}</span> {s.label}
              </button>
            ))}
          </div>
        </form>
      </div>
    </div>
  );
}
```


# src\app\(auth)\register\page.tsx

```tsx
'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authAPI, saveAuthSession, type RegisterPayload, type UserRole } from '@/lib/api/auth';

type RegisterForm = {
  role: UserRole;
  username: string;
  email: string;
  password: string;
  password2: string;
  first_name: string;
  last_name: string;
  phone: string;
  city: string;
  bio: string;
  portfolio_url: string;
  instagram: string;
  website: string;
  studio_name: string;
};

const initialForm: RegisterForm = {
  role: 'client',
  username: '',
  email: '',
  password: '',
  password2: '',
  first_name: '',
  last_name: '',
  phone: '',
  city: '',
  bio: '',
  portfolio_url: '',
  instagram: '',
  website: '',
  studio_name: '',
};

function getErrorMessage(error: unknown): string {
  if (
    typeof error === 'object' &&
    error !== null &&
    'response' in error
  ) {
    const response = (error as { response?: { data?: unknown; status?: number } }).response;

    if (response?.data) {
      const data = response.data;

      if (typeof data === 'string') return data;

      if (typeof data === 'object' && data !== null) {
        const values = Object.entries(data as Record<string, unknown>)
          .map(([key, value]) => {
            if (Array.isArray(value)) return `${key}: ${value.join('، ')}`;
            if (typeof value === 'string') return `${key}: ${value}`;
            return `${key}: ${JSON.stringify(value)}`;
          })
          .join(' | ');

        if (values) return values;
      }
    }

    if (response?.status) {
      return `خطای سرور با کد ${response.status}`;
    }
  }

  return 'ثبت‌نام با خطا مواجه شد. لطفاً اطلاعات را بررسی کنید.';
}

function hasTokenResponse(data: unknown) {
  if (typeof data !== 'object' || data === null) return false;

  const response = data as Record<string, unknown>;

  return Boolean(
    response.access ||
      response.access_token ||
      response.token ||
      response.refresh ||
      response.refresh_token
  );
}

export default function RegisterPage() {
  const router = useRouter();

  const [form, setForm] = useState<RegisterForm>(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isEditor = form.role === 'editor';
  const isStudio = form.role === 'studio';

  const isValid = useMemo(() => {
    return (
      form.username.trim().length >= 3 &&
      form.email.trim().length >= 5 &&
      form.password.length >= 6 &&
      form.password === form.password2
    );
  }, [form]);

  const setField = <K extends keyof RegisterForm>(key: K, value: RegisterForm[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const getRedirectPath = (role: UserRole) => {
    if (role === 'editor') return '/dashboard/orders';
    if (role === 'studio') return '/dashboard/orders';
    return '/dashboard/orders';
  };

  const handleRegister = async () => {
    setError('');

    if (!form.username.trim()) {
      setError('نام کاربری الزامی است.');
      return;
    }

    if (!form.email.trim()) {
      setError('ایمیل الزامی است.');
      return;
    }

    if (form.password.length < 6) {
      setError('رمز عبور باید حداقل ۶ کاراکتر باشد.');
      return;
    }

    if (form.password !== form.password2) {
      setError('تکرار رمز عبور با رمز عبور یکسان نیست.');
      return;
    }

    setLoading(true);

    try {
      const payload: RegisterPayload = {
        role: form.role,
        username: form.username.trim(),
        email: form.email.trim(),
        password: form.password,
        password2: form.password2,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        phone: form.phone.trim(),
        city: form.city.trim(),
      };

      if (isEditor || isStudio) {
        payload.bio = form.bio.trim();
        payload.portfolio_url = form.portfolio_url.trim();
        payload.instagram = form.instagram.trim();
        payload.website = form.website.trim();
      }

      if (isStudio) {
        payload.studio_name = form.studio_name.trim();
      }

      const registerResponse = await authAPI.register(payload);

      if (hasTokenResponse(registerResponse)) {
        saveAuthSession(registerResponse);
      } else {
        // اگر register فقط user ساخت ولی token نداد، بلافاصله login می‌کنیم.
        const loginResponse = await authAPI.login({
          username: form.username.trim(),
          password: form.password,
        });

        saveAuthSession(loginResponse);
      }

      router.push(getRedirectPath(form.role));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main
      className="min-h-screen px-4 py-10"
      style={{ background: 'linear-gradient(160deg,#FAFAFA 0%,#F3F0FE 50%,#FDF0F6 100%)' }}
    >
      <div className="mx-auto max-w-4xl">
        <div className="mb-8 text-center">
          <Link href="/" className="text-sm font-medium text-violet-700 hover:text-violet-800">
            بازگشت به خانه
          </Link>

          <h1 className="mt-5 text-3xl font-bold text-gray-900">
            ثبت‌نام در Retoucher
          </h1>

          <p className="mt-2 text-sm text-gray-600">
            نوع حساب خود را انتخاب کنید و اطلاعات لازم را وارد کنید.
          </p>
        </div>

        <section className="rounded-3xl bg-white p-6 shadow-sm md:p-8">
          <div className="mb-6 grid gap-3 md:grid-cols-3">
            <button
              type="button"
              onClick={() => setField('role', 'client')}
              className={`rounded-2xl border px-4 py-4 text-right transition ${
                form.role === 'client'
                  ? 'border-violet-300 bg-violet-50 text-violet-800'
                  : 'border-gray-100 bg-gray-50 text-gray-700 hover:bg-gray-100'
              }`}
            >
              <div className="font-bold">مشتری</div>
              <div className="mt-1 text-xs">ثبت سفارش و پیگیری پروژه‌ها</div>
            </button>

            <button
              type="button"
              onClick={() => setField('role', 'editor')}
              className={`rounded-2xl border px-4 py-4 text-right transition ${
                form.role === 'editor'
                  ? 'border-violet-300 bg-violet-50 text-violet-800'
                  : 'border-gray-100 bg-gray-50 text-gray-700 hover:bg-gray-100'
              }`}
            >
              <div className="font-bold">ادیتور</div>
              <div className="mt-1 text-xs">دریافت سفارش و تحویل کار</div>
            </button>

            <button
              type="button"
              onClick={() => setField('role', 'studio')}
              className={`rounded-2xl border px-4 py-4 text-right transition ${
                form.role === 'studio'
                  ? 'border-violet-300 bg-violet-50 text-violet-800'
                  : 'border-gray-100 bg-gray-50 text-gray-700 hover:bg-gray-100'
              }`}
            >
              <div className="font-bold">آتلیه / استودیو</div>
              <div className="mt-1 text-xs">مدیریت سفارش‌های عکاسی و روتوش</div>
            </button>
          </div>

          {error && (
            <div className="mb-5 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm leading-6 text-red-600">
              {error}
            </div>
          )}

          <div className="grid gap-5 md:grid-cols-2">
            <Field
              label="نام کاربری"
              value={form.username}
              onChange={(value) => setField('username', value)}
              placeholder="مثلاً faraz"
              required
            />

            <Field
              label="ایمیل"
              type="email"
              value={form.email}
              onChange={(value) => setField('email', value)}
              placeholder="example@email.com"
              required
            />

            <Field
              label="نام"
              value={form.first_name}
              onChange={(value) => setField('first_name', value)}
              placeholder="نام"
            />

            <Field
              label="نام خانوادگی"
              value={form.last_name}
              onChange={(value) => setField('last_name', value)}
              placeholder="نام خانوادگی"
            />

            <Field
              label="رمز عبور"
              type="password"
              value={form.password}
              onChange={(value) => setField('password', value)}
              placeholder="حداقل ۶ کاراکتر"
              required
            />

            <Field
              label="تکرار رمز عبور"
              type="password"
              value={form.password2}
              onChange={(value) => setField('password2', value)}
              placeholder="تکرار رمز عبور"
              required
            />

            <Field
              label="شماره تماس"
              value={form.phone}
              onChange={(value) => setField('phone', value)}
              placeholder="اختیاری"
            />

            <Field
              label="شهر"
              value={form.city}
              onChange={(value) => setField('city', value)}
              placeholder="اختیاری"
            />

            {isStudio && (
              <Field
                label="نام آتلیه / استودیو"
                value={form.studio_name}
                onChange={(value) => setField('studio_name', value)}
                placeholder="مثلاً آتلیه نور"
              />
            )}

            {(isEditor || isStudio) && (
              <>
                <Field
                  label="لینک نمونه‌کار"
                  value={form.portfolio_url}
                  onChange={(value) => setField('portfolio_url', value)}
                  placeholder="https://..."
                />

                <Field
                  label="اینستاگرام"
                  value={form.instagram}
                  onChange={(value) => setField('instagram', value)}
                  placeholder="@username"
                />

                <Field
                  label="وب‌سایت"
                  value={form.website}
                  onChange={(value) => setField('website', value)}
                  placeholder="https://..."
                />

                <div className="md:col-span-2">
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">
                    معرفی کوتاه
                  </label>
                  <textarea
                    value={form.bio}
                    onChange={(e) => setField('bio', e.target.value)}
                    rows={5}
                    placeholder="درباره تجربه، سبک کاری و مهارت‌ها..."
                    className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-violet-300"
                  />
                </div>
              </>
            )}
          </div>

          <button
            type="button"
            onClick={handleRegister}
            disabled={loading || !isValid}
            className="mt-7 w-full rounded-2xl bg-gray-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-50"
          >
            {loading ? 'در حال ثبت‌نام...' : 'ثبت‌نام و ورود'}
          </button>

          <div className="mt-5 text-center text-sm text-gray-600">
            قبلاً حساب دارید؟{' '}
            <Link href="/login" className="font-medium text-violet-700 hover:text-violet-800">
              ورود
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
  required?: boolean;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="mr-1 text-red-500">*</span>}
      </label>

      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-violet-300"
      />
    </div>
  );
}
```


# src\app\(auth)\forgot-password\page.tsx

```tsx
'use client';

import { useRef, useState } from 'react';
import Link from 'next/link';
import { Loader2, Mail, Lock } from 'lucide-react';
import { authAPI } from '../../../lib/api/auth';

type ForgotStep = 'email' | 'otp' | 'new-password' | 'done';

export default function ForgotPasswordPage() {
  const [step, setStep] = useState<ForgotStep>('email');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '']);
  const [newPass, setNewPass] = useState('');
  const [confirmPass, setConfirmPass] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleOtpInput = (idx: number, val: string) => {
    const cleaned = val.replace(/\D/, '');
    const next = [...otp];
    next[idx] = cleaned;
    setOtp(next);
    if (cleaned && idx < 4) otpRefs.current[idx + 1]?.focus();
  };

  const handleSendCode = async () => {
    if (!email.includes('@')) return;
    setLoading(true);
    try {
      await authAPI.forgotPassword(email);
      setStep('otp');
    } catch {
      setError('ایمیل یافت نشد.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    const code = otp.join('');
    if (code.length < 5) return;
    setLoading(true);
    try {
      await authAPI.verifyOTP(email, code);
      setStep('new-password');
    } catch {
      setError('کد اشتباه است.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPass = async () => {
    if (newPass.length < 6 || newPass !== confirmPass) {
      setError('رمزهای عبور یکسان نیستند.');
      return;
    }
    setLoading(true);
    try {
      await authAPI.resetPassword(otp.join(''), newPass);
      setStep('done');
    } catch {
      setError('خطا. دوباره تلاش کنید.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{ background: 'linear-gradient(160deg,#F3F0FE 0%,#FDF0F6 100%)' }}
    >
      <div className="auth-card w-full max-w-md p-8 text-center">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
          style={{ background: '#F3F0FE' }}
        >
          {step === 'done' ? '🎉' : step === 'new-password' ? <Lock size={28} style={{ color: '#9B85E8' }} /> : <Mail size={28} style={{ color: '#9B85E8' }} />}
        </div>

        {step === 'email' && (
          <>
            <h1 className="text-xl font-semibold text-gray-800">بازیابی رمز عبور</h1>
            <p className="text-sm mt-2 mb-6" style={{ color: '#7B7B90' }}>
              ایمیل خود را وارد کنید تا کد تایید برایتان ارسال شود
            </p>
            <div className="text-right mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1.5">ایمیل</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="input-auth w-full px-4 py-3 rounded-xl text-sm bg-gray-50 outline-none"
                style={{ fontFamily: 'inherit' }}
              />
            </div>
            {error && <p className="text-sm mb-3" style={{ color: '#E89B6D' }}>{error}</p>}
            <button
              onClick={handleSendCode}
              disabled={!email.includes('@') || loading}
              className="btn-auth-primary w-full py-3 rounded-xl text-white font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading && <Loader2 size={18} className="animate-spin" />}
              ارسال کد تایید
            </button>
            <Link href="/login" className="block mt-3 text-sm" style={{ color: '#9B85E8' }}>
              بازگشت به ورود
            </Link>
          </>
        )}

        {step === 'otp' && (
          <>
            <h1 className="text-xl font-semibold text-gray-800">کد تایید را وارد کنید</h1>
            <div className="text-sm mt-2 mb-2 p-3 rounded-xl flex items-center gap-2" style={{ background: '#EEF8F4', color: '#6DB89A' }}>
              <Mail size={16} /> کد ۵ رقمی به {email} ارسال شد
            </div>
            <div className="flex gap-3 justify-center my-6" dir="ltr">
              {otp.map((digit, idx) => (
                <input
                  key={idx}
                  ref={(el) => { otpRefs.current[idx] = el; }}
                  type="text"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleOtpInput(idx, e.target.value)}
                  className={`otp-input w-12 h-14 rounded-xl text-center text-xl font-bold outline-none ${digit ? 'filled' : ''}`}
                  style={{ fontFamily: 'monospace', border: '1.5px solid #EBEBF0', background: '#FAFAFA' }}
                />
              ))}
            </div>
            {error && <p className="text-sm mb-3" style={{ color: '#E89B6D' }}>{error}</p>}
            <button
              onClick={handleVerifyOTP}
              disabled={otp.join('').length < 5 || loading}
              className="btn-auth-primary w-full py-3 rounded-xl text-white font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading && <Loader2 size={18} className="animate-spin" />}
              تایید کد
            </button>
            <p className="text-sm mt-3" style={{ color: '#7B7B90' }}>
              کد دریافت نکردید؟{' '}
              <button onClick={() => { setStep('email'); setError(''); }} style={{ color: '#9B85E8', fontFamily: 'inherit' }}>
                ارسال مجدد
              </button>
            </p>
          </>
        )}

        {step === 'new-password' && (
          <>
            <h1 className="text-xl font-semibold text-gray-800">رمز عبور جدید</h1>
            <p className="text-sm mt-2 mb-6" style={{ color: '#7B7B90' }}>رمز عبور جدید خود را انتخاب کنید</p>
            <div className="space-y-3 text-right">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">رمز جدید</label>
                <input
                  type="password"
                  value={newPass}
                  onChange={(e) => setNewPass(e.target.value)}
                  placeholder="حداقل ۸ کاراکتر"
                  className="input-auth w-full px-4 py-2.5 rounded-xl text-sm bg-gray-50 outline-none"
                  style={{ fontFamily: 'inherit' }}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">تکرار رمز</label>
                <input
                  type="password"
                  value={confirmPass}
                  onChange={(e) => setConfirmPass(e.target.value)}
                  placeholder="رمز عبور را تکرار کنید"
                  className="input-auth w-full px-4 py-2.5 rounded-xl text-sm bg-gray-50 outline-none"
                  style={{ fontFamily: 'inherit' }}
                />
              </div>
            </div>
            {error && <p className="text-sm mt-3" style={{ color: '#E89B6D' }}>{error}</p>}
            <button
              onClick={handleResetPass}
              disabled={newPass.length < 6 || newPass !== confirmPass || loading}
              className="btn-auth-primary w-full mt-5 py-3 rounded-xl text-white font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading && <Loader2 size={18} className="animate-spin" />}
              ذخیره رمز عبور جدید
            </button>
          </>
        )}

        {step === 'done' && (
          <>
            <h1 className="text-xl font-semibold text-gray-800">رمز عبور تغییر کرد ✅</h1>
            <p className="text-sm mt-2 mb-6" style={{ color: '#7B7B90' }}>
              رمز عبور شما با موفقیت تغییر یافت. می‌توانید وارد شوید.
            </p>
            <Link href="/login" className="btn-auth-primary block w-full py-3 rounded-xl text-white font-semibold text-sm text-center">
              رفتن به ورود
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
```


# src\types\index.ts

```tsx
// ─── User & Auth ───
export interface User {
  id: number;
  username: string;
  email: string | null;
  phone_number: string | null;
  first_name: string;
  last_name: string;
  role: 'client' | 'editor' | 'admin' | 'studio' | 'supervisor' | string;
  is_verified: boolean;
  avatar?: string;
  date_joined: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  role: 'client' | 'editor' | 'studio';
  phone_number?: string;
}

// ─── Catalog ───
export interface EditCategory {
  id: number;
  title: string;
  slug: string;
  description: string;
  is_active: boolean;
}

export interface EditStyle {
  id: number;
  category: number;
  title: string;
  slug: string;
  description: string;
  min_price: number;
  max_price: number;
  suggested_price: number;
  estimated_delivery_hours: number;
}

// ─── Project Request ───
export type ProjectRequestType =
  | 'direct_editor'
  | 'public_quote'
  | 'sample_challenge'
  | 'managed_order';

export type ProjectRequestStatus =
  | 'draft'
  | 'submitted'
  | 'open_for_quotes'
  | 'open_for_samples'
  | 'waiting_for_editor'
  | 'under_review'
  | 'editor_selected'
  | 'converted_to_order'
  | 'cancelled'
  | 'expired';

export interface ProjectRequest {
  id: number;
  title: string;
  description: string;
  request_type: ProjectRequestType;
  status: ProjectRequestStatus;
  edit_style: number;
  budget_min?: number;
  budget_max?: number;
  deadline_days?: number;
  submitted_at?: string;
  expires_at?: string;
  is_expired: boolean;
  time_remaining_hours?: number;
  images: ProjectImage[];
  created_at: string;
}

export interface ProjectImage {
  id: number;
  image: string;
  caption: string;
  sort_order: number;
}

export interface CreateProjectPayload {
  title: string;
  description: string;
  request_type: ProjectRequestType;
  edit_style: number;
  budget_min?: number;
  budget_max?: number;
  deadline_days?: number;
}

// ─── Order ───
export type OrderStatus =
  | 'draft'
  | 'submitted'
  | 'in_review'
  | 'assigned'
  | 'in_progress'
  | 'delivered'
  | 'cancelled'
  | 'client_review'
  | 'revision_required'
  | 'client_revision_requested'
  | 'completed'
  | 'settlement_pending'
  | 'paid'
  | 'closed';

export interface OrderImage {
  id: number;
  image: string;
  note: string;
  uploaded_at: string;
}

export interface OrderDelivery {
  id: number;
  order: number;
  file: string;
  note: string;
  uploaded_by: number | null;
  uploaded_by_username: string | null;
  uploaded_at: string;
  publication_status: 'private' | 'requested' | 'approved' | 'rejected';
  publication_requested_by: number | null;
  publication_requested_at: string | null;
  publication_reviewed_by: number | null;
  publication_reviewed_at: string | null;
  publication_note: string;
  is_public: boolean;
}

export interface OrderRevision {
  id: number;
  source: 'supervisor' | 'client';
  note: string;
  requested_by: number | null;
  requested_by_username: string | null;
  created_at: string;
}

export interface OrderRating {
  id: number;
  source: 'supervisor' | 'client';
  score: number;
  comment: string;
  rated_by: number | null;
  rated_by_username: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderComment {
  id: number;
  order: number;
  sender: number | null;
  sender_username: string | null;
  target_type: 'order' | 'image' | 'delivery' | 'revision';
  image: number | null;
  delivery: number | null;
  revision: number | null;
  text: string;
  x: number | null;
  y: number | null;
  status: 'active' | 'resolved' | 'approved' | 'deleted';
  is_edited: boolean;
  edited_at: string | null;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
  parent: number | null;
  parent_text: string | null;
  parent_sender_username: string | null;
  is_resolved: boolean;
  resolved_by: number | null;
  resolved_by_username: string | null;
  resolved_at: string | null;
  annotation_type: 'none' | 'point' | 'rectangle' | 'circle' | 'arrow' | 'freehand';
  annotation_label: string;
  annotation_color: string;
  annotation_data: Record<string, unknown>;
  is_publicly_visible: boolean;
  replies?: OrderComment[];
}

export interface OrderStatusHistory {
  id: number;
  order: number;
  changed_by: number | null;
  changed_by_username: string | null;
  from_status: string;
  to_status: string;
  note: string;
  created_at: string;
}

export interface OrderActivityLog {
  id: number;
  order: number;
  actor: number | null;
  actor_username: string | null;
  activity_type: string;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface Order {
  id: number;

  client: number;
  client_username: string;

  editor: number | null;
  editor_username: string | null;

  title: string;
  description?: string;

  status: OrderStatus;
  revision_count: number;

  supervisor_approved_at: string | null;
  client_approved_at: string | null;
  settlement_started_at?: string | null;
  paid_at?: string | null;
  closed_at?: string | null;

  deadline: string | null;

  images?: OrderImage[];
  deliveries?: OrderDelivery[];
  revisions?: OrderRevision[];
  ratings?: OrderRating[];
  comments?: OrderComment[];
  status_history?: OrderStatusHistory[];
  activity_logs?: OrderActivityLog[];

  created_at: string;
  updated_at: string;
}



// ─── Wallet ───
export interface Wallet {
  id: number;
  balance: string;
  user: number;
}

export interface Transaction {
  id: number;
  tx_type: string;
  amount: number;
  description: string;
  created_at: string;
}

// ─── API Response ───
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  [key: string]: unknown;
}

// ─── Editors ───
export interface EditorProfile {
  id: number;
  user?: number;
  full_name?: string;
  display_name?: string;
  first_name?: string;
  last_name?: string;
  username?: string;
  email?: string;
  avatar?: string | null;
  profile_image?: string | null;
  bio?: string;
  about?: string;
  city?: string | null;
  province?: string | null;
  rating?: number;
  average_rating?: number;
  completed_orders?: number;
  orders_completed?: number;
  specialties?: string[];
  skills?: string[];
  portfolio?: Array<{
    id: number;
    title?: string;
    image?: string;
    before_image?: string;
    after_image?: string;
    description?: string;
  }>;
}
```
