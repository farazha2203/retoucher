

## src\app\(auth)\forgot-password\page.tsx

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


## src\app\(auth)\login\page.tsx

```tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { authAPI } from "../../../lib/api/auth";
import { useAuthStore } from "../../../lib/stores/auth.store";

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();

  const [form, setForm] = useState({ email: "", password: "" });
  const [showPass, setShowPass] = useState(false);
  const [remember, setRemember] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isValid = form.email.trim().length >= 3 && form.password.length >= 6;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;
    setLoading(true);
    setError("");
    try {
      const data = await authAPI.login({
        username: form.email.trim(),
        password: form.password,
      });
      const me = await authAPI.getMe();
      setAuth(me, data.access, data.refresh);
      router.push("/dashboard/orders");
    } catch {
      setError("ایمیل یا رمز عبور اشتباه است.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left Art Panel */}
      <div
        className="hidden lg:flex flex-1 flex-col items-center justify-center p-12 relative overflow-hidden"
        style={{
          background:
            "linear-gradient(145deg,#FDF0F6 0%,#F3F0FE 40%,#EEF8F4 100%)",
        }}
      >
        <div
          className="absolute -top-20 -right-20 w-72 h-72 rounded-full"
          style={{ background: "rgba(196,181,244,.2)" }}
        />
        <div
          className="absolute -bottom-16 -left-16 w-56 h-56 rounded-full"
          style={{ background: "rgba(168,213,194,.2)" }}
        />
        <div className="relative z-10 text-center">
          <div className="text-4xl font-semibold text-gray-800 leading-snug">
            خلاقیت را
            <br />
            <span style={{ color: "#E07AA0" }}>حرفه‌ای</span> بفروش
          </div>
          <p className="mt-4 text-gray-500 text-sm leading-relaxed max-w-xs mx-auto">
            مارکت‌پلیس تخصصی روتوش، ادیت عکس و هوش مصنوعی تصویری
          </p>
          <div className="flex flex-wrap gap-2 mt-8 justify-center">
            {[
              { label: "روتوش حرفه‌ای", bg: "#FDF0F6", color: "#E07AA0" },
              { label: "ادیت عکس", bg: "#F3F0FE", color: "#9B85E8" },
              { label: "هوش مصنوعی", bg: "#EEF8F4", color: "#6DB89A" },
              { label: "آتلیه", bg: "#FEF5F0", color: "#E89B6D" },
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
        style={{ background: "white" }}
      >
        <form onSubmit={handleSubmit} className="w-full max-w-sm">
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-6">
              <div
                className="w-8 h-8 rounded-xl flex items-center justify-center text-base"
                style={{
                  background: "linear-gradient(135deg,#F2A8C4,#C4B5F4)",
                }}
              >
                ✦
              </div>
              <span className="font-semibold text-lg text-gray-800">
                ریتاچر
              </span>
            </div>
            <h1 className="text-2xl font-semibold text-gray-800">
              خوش برگشتی 👋
            </h1>
            <p className="mt-2 text-sm" style={{ color: "#7B7B90" }}>
              حساب ندارید؟{" "}
              <Link
                href="/register"
                style={{ color: "#9B85E8" }}
                className="font-medium"
              >
                ثبت‌نام کنید
              </Link>
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                نام کاربری یا ایمیل
              </label>
              <input
                type="text"
                value={form.email}
                onChange={(e) =>
                  setForm((f) => ({ ...f, email: e.target.value }))
                }
                placeholder="name@example.com"
                className="input-auth w-full px-4 py-3 rounded-xl text-sm bg-gray-50 outline-none"
                style={{ fontFamily: "inherit" }}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                رمز عبور
              </label>
              <div className="relative">
                <input
                  type={showPass ? "text" : "password"}
                  value={form.password}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, password: e.target.value }))
                  }
                  placeholder="حداقل ۸ کاراکتر"
                  className="input-auth w-full px-4 py-3 rounded-xl text-sm bg-gray-50 outline-none pr-10"
                  style={{ fontFamily: "inherit" }}
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
              <span className="text-sm" style={{ color: "#7B7B90" }}>
                مرا به خاطر بسپار
              </span>
            </label>
            <Link
              href="/forgot-password"
              className="text-sm font-medium"
              style={{ color: "#9B85E8" }}
            >
              فراموش کردید؟
            </Link>
          </div>

          {error && (
            <div
              className="mb-4 p-3 rounded-xl text-sm"
              style={{
                background: "#FEF5F0",
                color: "#E89B6D",
                border: "1px solid rgba(232,155,109,.3)",
              }}
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
            {loading ? "در حال ورود..." : "ورود به حساب"}
          </button>

          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-gray-100" />
            <span className="text-xs text-gray-400">یا</span>
            <div className="flex-1 h-px bg-gray-100" />
          </div>

          <div className="flex gap-3">
            {[
              { icon: "🔵", label: "Google" },
              { icon: "⚫", label: "Apple" },
            ].map((s) => (
              <button
                key={s.label}
                type="button"
                className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium border transition-colors hover:bg-gray-50"
                style={{
                  borderColor: "#EBEBF0",
                  color: "#2D2D3A",
                  fontFamily: "inherit",
                }}
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


## src\app\(auth)\register\page.tsx

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


## src\app\(auth)\layout.tsx

```tsx
import type { ReactNode } from 'react';
import '../../styles/auth.css';

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen" style={{ fontFamily: 'var(--font-vazirmatn), system-ui' }}>
      {children}
    </div>
  );
}
```


## src\app\dashboard\orders\[id]\page.tsx

```tsx
```


## src\app\dashboard\orders\page.tsx

```tsx
'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ordersAPI } from '@/lib/api/orders';
import type { Order, OrderStatus } from '@/types';

const statusLabels: Record<OrderStatus, string> = {
  draft: 'پیش‌نویس',
  submitted: 'ثبت‌شده',
  in_review: 'در حال بررسی',
  assigned: 'اختصاص داده‌شده',
  in_progress: 'در حال انجام',
  delivered: 'تحویل‌شده',
  cancelled: 'لغوشده',
  client_review: 'بررسی کارفرما',
  revision_required: 'نیازمند اصلاح',
  client_revision_requested: 'درخواست اصلاح کارفرما',
  completed: 'تکمیل‌شده',
  settlement_pending: 'در انتظار تسویه',
  paid: 'پرداخت‌شده',
  closed: 'بسته‌شده',
};

const statusStyles: Record<OrderStatus, string> = {
  draft: 'bg-gray-100 text-gray-700',
  submitted: 'bg-blue-50 text-blue-700',
  in_review: 'bg-indigo-50 text-indigo-700',
  assigned: 'bg-violet-50 text-violet-700',
  in_progress: 'bg-amber-50 text-amber-700',
  delivered: 'bg-cyan-50 text-cyan-700',
  cancelled: 'bg-red-50 text-red-700',
  client_review: 'bg-purple-50 text-purple-700',
  revision_required: 'bg-orange-50 text-orange-700',
  client_revision_requested: 'bg-orange-50 text-orange-700',
  completed: 'bg-emerald-50 text-emerald-700',
  settlement_pending: 'bg-yellow-50 text-yellow-700',
  paid: 'bg-green-50 text-green-700',
  closed: 'bg-slate-100 text-slate-700',
};

function formatDate(value?: string | null) {
  if (!value) return '-';

  try {
    return new Intl.DateTimeFormat('fa-IR', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function getStatusLabel(status: OrderStatus) {
  return statusLabels[status] || status;
}

function getStatusClass(status: OrderStatus) {
  return statusStyles[status] || 'bg-gray-100 text-gray-700';
}

export default function DashboardOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | OrderStatus>('all');

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      setLoading(true);
      setError('');

      try {
        const data = await ordersAPI.list();
        if (mounted) setOrders(data.results);
      } catch {
        if (mounted) setError('دریافت سفارش‌ها با خطا مواجه شد.');
      } finally {
        if (mounted) setLoading(false);
      }
    };

    load();

    return () => {
      mounted = false;
    };
  }, []);

  const filteredOrders = useMemo(() => {
    if (statusFilter === 'all') return orders;
    return orders.filter((order) => order.status === statusFilter);
  }, [orders, statusFilter]);

  return (
    <main
      className="min-h-screen px-4 py-10"
      style={{ background: 'linear-gradient(160deg,#FAFAFA 0%,#F3F0FE 50%,#FDF0F6 100%)' }}
    >
      <div className="mx-auto max-w-6xl">
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">سفارش‌های من</h1>
            <p className="mt-2 text-sm text-gray-600">
              وضعیت سفارش‌ها، تحویل، اصلاحات و تاییدها را از اینجا پیگیری کنید.
            </p>
          </div>

          <Link
            href="/orders/new"
            className="rounded-2xl bg-gray-900 px-5 py-3 text-center text-sm font-medium text-white transition hover:bg-gray-800"
          >
            ثبت سفارش جدید
          </Link>
        </div>

        <div className="mb-6 overflow-x-auto rounded-2xl bg-white p-3 shadow-sm">
          <div className="flex min-w-max gap-2">
            <button
              type="button"
              onClick={() => setStatusFilter('all')}
              className={`rounded-xl px-4 py-2 text-sm font-medium transition ${
                statusFilter === 'all'
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
              }`}
            >
              همه
            </button>

            {(Object.keys(statusLabels) as OrderStatus[]).map((status) => (
              <button
                key={status}
                type="button"
                onClick={() => setStatusFilter(status)}
                className={`rounded-xl px-4 py-2 text-sm font-medium transition ${
                  statusFilter === status
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                }`}
              >
                {statusLabels[status]}
              </button>
            ))}
          </div>
        </div>

        {loading && (
          <div className="rounded-3xl bg-white p-8 text-center shadow-sm">
            <p className="text-sm text-gray-500">در حال دریافت سفارش‌ها...</p>
          </div>
        )}

        {!loading && error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-center text-sm text-red-600">
            {error}
          </div>
        )}

        {!loading && !error && filteredOrders.length === 0 && (
          <div className="rounded-3xl bg-white p-8 text-center shadow-sm">
            <p className="text-sm text-gray-500">سفارشی برای نمایش وجود ندارد.</p>

            <Link
              href="/orders/new"
              className="mt-5 inline-flex rounded-2xl bg-gray-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-gray-800"
            >
              اولین سفارش را ثبت کنید
            </Link>
          </div>
        )}

        {!loading && !error && filteredOrders.length > 0 && (
          <div className="grid gap-5">
            {filteredOrders.map((order) => (
              <article
                key={order.id}
                className="rounded-3xl border border-gray-100 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div className="min-w-0">
                    <div className="mb-3 flex flex-wrap items-center gap-2">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${getStatusClass(order.status)}`}
                      >
                        {getStatusLabel(order.status)}
                      </span>

                      {order.editor_username && (
                        <span className="rounded-full bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700">
                          ادیتور: {order.editor_username}
                        </span>
                      )}
                    </div>

                    <h2 className="text-xl font-bold text-gray-900">{order.title}</h2>

                    <p className="mt-2 text-sm text-gray-500">
                      شناسه سفارش: #{order.id}
                    </p>
                  </div>

                  <div className="shrink-0 text-right">
                    <div className="text-sm text-gray-500">کارفرما</div>
                    <div className="mt-1 font-bold text-gray-900">
                      {order.client_username || `#${order.client}`}
                    </div>
                  </div>
                </div>

                <div className="mt-5 grid gap-3 border-t border-gray-100 pt-5 text-sm sm:grid-cols-4">
                  <div>
                    <div className="text-xs text-gray-400">تاریخ ثبت</div>
                    <div className="mt-1 font-medium text-gray-700">{formatDate(order.created_at)}</div>
                  </div>

                  <div>
                    <div className="text-xs text-gray-400">ددلاین</div>
                    <div className="mt-1 font-medium text-gray-700">{formatDate(order.deadline)}</div>
                  </div>

                  <div>
                    <div className="text-xs text-gray-400">تعداد اصلاحات</div>
                    <div className="mt-1 font-medium text-gray-700">{order.revision_count || 0}</div>
                  </div>

                  <div>
                    <div className="text-xs text-gray-400">آخرین بروزرسانی</div>
                    <div className="mt-1 font-medium text-gray-700">{formatDate(order.updated_at)}</div>
                  </div>
                </div>

                <div className="mt-5 flex flex-wrap gap-3">
                  <Link
                    href={`/dashboard/orders/${order.id}`}
                    className="rounded-2xl bg-gray-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-gray-800"
                  >
                    مشاهده جزئیات
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
```


## src\app\editors\[id]\page.tsx

```tsx
```


## src\app\editors\page.tsx

```tsx
'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { editorsAPI, type EditorProfile } from '@/lib/api/editors';

function getEditorName(editor: EditorProfile) {
  return editor.display_name || editor.username || `ادیتور #${editor.id}`;
}

function getLevelLabel(level: EditorProfile['level']) {
  switch (level) {
    case 'junior':
      return 'جونیور';
    case 'mid':
      return 'مید';
    case 'senior':
      return 'سینیور';
    case 'pro':
      return 'پرو';
    default:
      return level;
  }
}

export default function EditorsPage() {
  const [items, setItems] = useState<EditorProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await editorsAPI.list();
        if (mounted) setItems(data);
      } catch {
        if (mounted) setError('دریافت لیست ادیتورها با خطا مواجه شد.');
      } finally {
        if (mounted) setLoading(false);
      }
    };

    load();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <main
      className="min-h-screen px-4 py-10"
      style={{ background: 'linear-gradient(160deg,#FAFAFA 0%,#F3F0FE 50%,#FDF0F6 100%)' }}
    >
      <div className="mx-auto max-w-6xl">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900">ادیتورهای حرفه‌ای</h1>
          <p className="mt-2 text-sm text-gray-600">
            ادیتور مناسب پروژه‌ات را پیدا کن و نمونه‌کارها را بررسی کن.
          </p>
        </div>

        {loading && (
          <div className="rounded-2xl bg-white p-8 text-center shadow-sm">
            <p className="text-sm text-gray-500">در حال دریافت ادیتورها...</p>
          </div>
        )}

        {!loading && error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-center text-sm text-red-600">
            {error}
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <div className="rounded-2xl bg-white p-8 text-center shadow-sm">
            <p className="text-sm text-gray-500">فعلاً ادیتوری برای نمایش وجود ندارد.</p>
          </div>
        )}

        {!loading && !error && items.length > 0 && (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((editor) => {
              const name = getEditorName(editor);

              return (
                <article
                  key={editor.id}
                  className="rounded-3xl border border-gray-100 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg"
                >
                  <div className="mb-4 flex items-center gap-4">
                    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-violet-100 text-xl font-bold text-violet-700">
                      {name.charAt(0)}
                    </div>

                    <div className="min-w-0 flex-1">
                      <h2 className="truncate text-lg font-semibold text-gray-900">{name}</h2>
                      <p className="mt-1 text-sm text-gray-500">سطح: {getLevelLabel(editor.level)}</p>
                    </div>
                  </div>

                  <p className="mb-4 line-clamp-3 text-sm leading-6 text-gray-600">
                    {editor.bio || 'هنوز توضیحی برای این ادیتور ثبت نشده است.'}
                  </p>

                  <div className="mb-4 flex flex-wrap gap-2">
                    {editor.skills.slice(0, 3).map((skill) => (
                      <span
                        key={skill.id}
                        className="rounded-full bg-violet-50 px-3 py-1 text-xs font-medium text-violet-700"
                      >
                        {skill.title}
                      </span>
                    ))}
                  </div>

                  <div className="mb-5 grid grid-cols-2 gap-3 text-sm">
                    <div className="rounded-xl bg-gray-50 p-3 text-center">
                      <div className="font-bold text-gray-900">
                        {Number(editor.rating_average || 0).toFixed(1)}
                      </div>
                      <div className="mt-1 text-xs text-gray-500">امتیاز</div>
                    </div>
                    <div className="rounded-xl bg-gray-50 p-3 text-center">
                      <div className="font-bold text-gray-900">{editor.completed_orders_count}</div>
                      <div className="mt-1 text-xs text-gray-500">پروژه تکمیل‌شده</div>
                    </div>
                  </div>

                  <div className="mb-5 grid grid-cols-2 gap-3 text-sm">
                    <div className="rounded-xl bg-gray-50 p-3 text-center">
                      <div className="font-bold text-gray-900">
                        {editor.base_price.toLocaleString('fa-IR')}
                      </div>
                      <div className="mt-1 text-xs text-gray-500">قیمت پایه</div>
                    </div>
                    <div className="rounded-xl bg-gray-50 p-3 text-center">
                      <div className="font-bold text-gray-900">{editor.average_delivery_hours} ساعت</div>
                      <div className="mt-1 text-xs text-gray-500">تحویل میانگین</div>
                    </div>
                  </div>

                  <Link
                    href={`/editors/${editor.id}`}
                    className="block rounded-2xl bg-gray-900 px-4 py-3 text-center text-sm font-medium text-white transition hover:bg-gray-800"
                  >
                    مشاهده پروفایل
                  </Link>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}
```


## src\app\orders\new\NewOrderClient.tsx

```tsx
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { ordersAPI } from '@/lib/api/orders';

export default function NewOrderClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const editorId = searchParams.get('editor');

  const [form, setForm] = useState({
    title: '',
    description: '',
    deadline: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isValid = form.title.trim().length >= 3;

  const handleSubmit = async () => {
    if (!isValid) {
      setError('عنوان سفارش باید حداقل ۳ کاراکتر باشد.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const payload = {
        title: form.title.trim(),
        description: form.description.trim(),
        deadline: form.deadline ? new Date(form.deadline).toISOString() : null,
      };

      const order = await ordersAPI.create(payload);
      router.push(`/dashboard/orders/${order.id}`);
    } catch {
      setError('ثبت سفارش با خطا مواجه شد. لطفاً اطلاعات را بررسی کنید.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main
      className="min-h-screen px-4 py-10"
      style={{ background: 'linear-gradient(160deg,#FAFAFA 0%,#F3F0FE 50%,#FDF0F6 100%)' }}
    >
      <div className="mx-auto max-w-3xl">
        <div className="mb-6">
          <Link
            href="/dashboard/orders"
            className="text-sm font-medium text-violet-700 hover:text-violet-800"
          >
            ← بازگشت به سفارش‌ها
          </Link>
        </div>

        <section className="rounded-3xl bg-white p-8 shadow-sm">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">ثبت سفارش جدید</h1>
            <p className="mt-2 text-sm text-gray-600">
              اطلاعات اولیه سفارش را وارد کنید تا سفارش شما ثبت و وارد روند بررسی شود.
            </p>

            {editorId && (
              <div className="mt-4 rounded-2xl border border-violet-100 bg-violet-50 p-4 text-sm text-violet-700">
                این سفارش از پروفایل ادیتور #{editorId} شروع شده است.
                <br />
                اتصال مستقیم سفارش به ادیتور در مرحله بعدی backend فعال می‌شود.
              </div>
            )}
          </div>

          {error && (
            <div className="mb-5 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-600">
              {error}
            </div>
          )}

          <div className="space-y-5">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                عنوان سفارش
              </label>
              <input
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                placeholder="مثلاً روتوش ۲۰ عکس پرتره"
                className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-violet-300"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                توضیحات سفارش
              </label>
              <textarea
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                rows={6}
                placeholder="جزئیات کار، سبک موردنظر، تعداد عکس‌ها و نکات مهم..."
                className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-violet-300"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                ددلاین
              </label>
              <input
                type="datetime-local"
                value={form.deadline}
                onChange={(e) => setForm((f) => ({ ...f, deadline: e.target.value }))}
                className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-violet-300"
              />
            </div>

            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading || !isValid}
              className="w-full rounded-2xl bg-gray-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-50"
            >
              {loading ? 'در حال ثبت سفارش...' : 'ثبت سفارش'}
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
```


## src\app\orders\new\page.tsx

```tsx
import { Suspense } from 'react';
import NewOrderClient from './NewOrderClient';

export default function NewOrderPage() {
  return (
    <Suspense
      fallback={
        <main
          className="min-h-screen px-4 py-10"
          style={{ background: 'linear-gradient(160deg,#FAFAFA 0%,#F3F0FE 50%,#FDF0F6 100%)' }}
        >
          <div className="mx-auto max-w-3xl">
            <section className="rounded-3xl bg-white p-8 text-center shadow-sm">
              <p className="text-sm text-gray-500">در حال آماده‌سازی فرم سفارش...</p>
            </section>
          </div>
        </main>
      }
    >
      <NewOrderClient />
    </Suspense>
  );
}
```


## src\app\globals.css

```tsx
@import "tailwindcss";

/* --- RTL + Font --- */

body {
  font-family: var(--font-vazirmatn), "Vazirmatn", system-ui, sans-serif;
}

html {
  direction: rtl;
}

html[dir="rtl"] {
  text-align: right;
}
```


## src\app\layout.tsx

```tsx
import type { Metadata } from 'next';
import { Vazirmatn } from 'next/font/google';
import { Providers } from './providers';
import './globals.css';

const vazirmatn = Vazirmatn({
  subsets: ['arabic'],
  variable: '--font-vazirmatn',
  display: 'swap',
  weight: ['300', '400', '500', '600', '700', '800', '900'],
});

export const metadata: Metadata = {
  title: {
    default: 'ریتاچر | مارکت‌پلیس تخصصی روتوش و ادیت عکس',
    template: '%s | ریتاچر',
  },
  description:
    'ریتاچر بهترین مارکت‌پلیس برای یافتن ادیتورهای حرفه‌ای روتوش، ادیت عکس، آتلیه و هوش مصنوعی تصویری. سفارش دهید، تحویل بگیرید.',
  keywords: [
    'روتوش عکس', 'ادیت عکس', 'فتوشاپ', 'لایت‌روم',
    'مارکت‌پلیس ادیتور', 'خدمات تصویری', 'هوش مصنوعی تصویری',
    'آتلیه', 'روتوشر', 'ریتاچر',
  ],
  authors: [{ name: 'ریتاچر', url: 'https://retoucher.ir' }],
  creator: 'ریتاچر',
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
  openGraph: {
    title: 'ریتاچر | مارکت‌پلیس تخصصی روتوش و ادیت عکس',
    description: 'بهترین ادیتورهای حرفه‌ای را در یک کلیک پیدا کنید',
    type: 'website',
    locale: 'fa_IR',
    siteName: 'ریتاچر',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ریتاچر',
    description: 'مارکت‌پلیس تخصصی روتوش و ادیت عکس',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, 'max-image-preview': 'large' },
  },
  alternates: { canonical: '/' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fa" dir="rtl">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
      </head>
      <body className={`${vazirmatn.variable} font-sans antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```


## src\app\page.tsx

```tsx
import type { Metadata } from 'next';
import LandingPageClient from '@/components/LandingPageClient';

export const metadata: Metadata = {
  title: 'ریتاچر | مارکت‌پلیس تخصصی روتوش و ادیت عکس',
  description:
    'بهترین ادیتورهای حرفه‌ای روتوش و ادیت عکس را در ریتاچر پیدا کنید. ثبت سفارش رایگان، تحویل سریع، پرداخت امن.',
};

export default function Page() {
  return <LandingPageClient />;
}
```


## src\app\providers.tsx

```tsx
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```


## src\components\layout\Footer.tsx

```tsx
import Link from 'next/link';

export function Footer() {
  return (
    <footer style={{ background: '#3D3022', color: 'rgba(255,255,255,.7)', padding: '4rem 1.5rem 2rem' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: '3rem', marginBottom: '3rem' }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 800, color: 'white', marginBottom: '.75rem' }}>✦ ریتاچر</div>
            <p style={{ fontSize: 13, lineHeight: 1.9 }}>مارکت‌پلیس تخصصی روتوش، ادیت عکس و خدمات هوش مصنوعی تصویری در ایران.</p>
            <p style={{ fontSize: 12, marginTop: '.5rem', color: 'rgba(255,255,255,.4)' }}>هر تصویر، یک داستان می‌گوید.</p>
          </div>
          {[
            {
              title: 'خدمات',
              links: ['روتوش عکس', 'ادیت رنگ', 'هوش مصنوعی', 'آتلیه', 'ویدئو'],
            },
            {
              title: 'شرکت',
              links: ['درباره ما', 'وبلاگ', 'کارفرماها', 'ادیتورها', 'تماس'],
            },
            {
              title: 'پشتیبانی',
              links: ['مرکز راهنما', 'شرایط استفاده', 'حریم خصوصی', 'گزارش تخلف'],
            },
          ].map((col) => (
            <div key={col.title}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'white', marginBottom: '1rem' }}>{col.title}</div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '.6rem' }}>
                {col.links.map((link) => (
                  <li key={link}>
                    <Link
                      href="/"
                      style={{ color: 'rgba(255,255,255,.6)', fontSize: 13, textDecoration: 'none' }}
                    >
                      {link}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div style={{
          borderTop: '1px solid rgba(255,255,255,.1)',
          paddingTop: '1.5rem',
          display: 'flex', justifyContent: 'space-between',
          alignItems: 'center', flexWrap: 'wrap', gap: '1rem',
        }}>
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,.4)' }}>
            © {new Date().getFullYear()} ریتاچر. تمامی حقوق محفوظ است.
          </p>
          <div style={{ display: 'flex', gap: 10 }}>
            {['📷', '💬', '🐦'].map((icon) => (
              <div key={icon} style={{
                width: 32, height: 32, borderRadius: 8,
                background: 'rgba(255,255,255,.1)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: 'pointer', fontSize: 14,
              }}>{icon}</div>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
```


## src\components\layout\Navbar.tsx

```tsx
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/lib/stores/auth.store';
import { Menu, X, User, LogOut, LayoutDashboard } from 'lucide-react';

export function Navbar() {
  const { isAuthenticated, user, clearAuth } = useAuthStore();
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [dropOpen, setDropOpen] = useState(false);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', fn);
    return () => window.removeEventListener('scroll', fn);
  }, []);

  return (
    <nav
      style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: scrolled ? 'rgba(255,255,255,.97)' : 'rgba(255,255,255,.9)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid #EDE5D8',
        transition: 'all .3s',
        boxShadow: scrolled ? '0 2px 20px rgba(0,0,0,.06)' : 'none',
      }}
    >
      <div
        style={{
          maxWidth: 1200, margin: '0 auto',
          padding: '0 1.5rem',
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between',
          height: 68,
        }}
      >
        {/* Logo */}
        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: '#3D3022',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'white', fontWeight: 900, fontSize: 17,
          }}>R</div>
          <span style={{ fontSize: 18, fontWeight: 800, color: '#3D3022' }}>ریتاچر</span>
        </Link>

        {/* Desktop Links */}
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }} className="hidden-mobile">
          {[
            { href: '/#services', label: 'خدمات' },
            { href: '/#how', label: 'نحوه کار' },
            { href: '/#editors', label: 'ادیتورها' },
            { href: '/#pricing', label: 'قیمت‌ها' },
          ].map((link) => (
            <Link
              key={link.href}
              href={link.href}
              style={{ fontSize: 14, fontWeight: 500, color: '#5C5C5C', textDecoration: 'none' }}
              onMouseEnter={(e) => (e.currentTarget.style.color = '#5C4A32')}
              onMouseLeave={(e) => (e.currentTarget.style.color = '#5C5C5C')}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {isAuthenticated && user ? (
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setDropOpen(!dropOpen)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '8px 14px', borderRadius: 10,
                  border: '1.5px solid #EDE5D8',
                  background: 'white', cursor: 'pointer',
                  fontSize: 13, fontWeight: 600, color: '#3D3022',
                  fontFamily: 'inherit',
                }}
              >
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: '#5C4A32', color: 'white',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 12, fontWeight: 700,
                }}>
                  {user.first_name?.[0] || user.username[0]}
                </div>
                {user.first_name || user.username}
              </button>

              {dropOpen && (
                <div style={{
                  position: 'absolute', top: '110%', left: 0,
                  background: 'white', borderRadius: 12,
                  border: '1px solid #EDE5D8',
                  boxShadow: '0 8px 24px rgba(0,0,0,.1)',
                  minWidth: 180, padding: '8px 0',
                  zIndex: 200,
                }}>
                  <Link href="/dashboard" style={dropItemStyle} onClick={() => setDropOpen(false)}>
                    <LayoutDashboard size={15} /> داشبورد
                  </Link>
                  <Link href="/dashboard/profile" style={dropItemStyle} onClick={() => setDropOpen(false)}>
                    <User size={15} /> پروفایل
                  </Link>
                  <hr style={{ margin: '6px 12px', borderColor: '#EDE5D8' }} />
                  <button
                    style={{ ...dropItemStyle, width: '100%', textAlign: 'right', background: 'none', border: 'none', cursor: 'pointer', color: '#E07070' }}
                    onClick={() => { clearAuth(); setDropOpen(false); }}
                  >
                    <LogOut size={15} /> خروج
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link href="/login" style={{
                padding: '8px 18px', borderRadius: 8,
                border: '1.5px solid #EDE5D8', background: 'transparent',
                fontSize: 13, fontWeight: 600, color: '#5C4A32', textDecoration: 'none',
              }}>
                ورود
              </Link>
              <Link href="/register" style={{
                padding: '8px 18px', borderRadius: 8,
                background: '#3D3022', color: 'white',
                fontSize: 13, fontWeight: 600, textDecoration: 'none',
                transition: 'background .2s',
              }}>
                شروع رایگان ↗
              </Link>
            </>
          )}

          {/* Mobile menu button */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="show-mobile"
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4, color: '#3D3022' }}
          >
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {menuOpen && (
        <div style={{
          padding: '1rem 1.5rem 1.5rem',
          borderTop: '1px solid #EDE5D8',
          display: 'flex', flexDirection: 'column', gap: 12,
          background: 'white',
        }}>
          {['خدمات', 'نحوه کار', 'ادیتورها', 'قیمت‌ها'].map((label) => (
            <Link
              key={label}
              href={`/#${label}`}
              style={{ fontSize: 15, color: '#5C5C5C', textDecoration: 'none', padding: '6px 0' }}
              onClick={() => setMenuOpen(false)}
            >
              {label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}

const dropItemStyle: React.CSSProperties = {
  display: 'flex', alignItems: 'center', gap: 8,
  padding: '9px 16px', fontSize: 13, fontWeight: 500,
  color: '#3D3022', textDecoration: 'none',
  transition: 'background .15s',
};
```


## src\components\LandingPageClient.tsx

```tsx
'use client';

import Link from 'next/link';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';

export default function LandingPageClient() {
  return (
    <>
      <Navbar />
      <main>
        <HeroSection />
        <TrustBar />
        <ServicesSection />
        <HowItWorks />
        <EditorTypesSection />
        <PricingSection />
        <TestimonialsSection />
        <CTASection />
      </main>
      <Footer />
    </>
  );
}

// ─── Hero ───────────────────────────────────────────
function HeroSection() {
  return (
    <section
      id="hero"
      style={{
        background: 'linear-gradient(160deg,#F9F5EF 0%,#EBF4EE 50%,#E8EFF8 100%)',
        padding: 'clamp(4rem,8vw,7rem) 1.5rem 4rem',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: -100,
          right: -100,
          width: 400,
          height: 400,
          borderRadius: '50%',
          background: 'rgba(92,74,50,.05)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: -80,
          left: -80,
          width: 300,
          height: 300,
          borderRadius: '50%',
          background: 'rgba(45,90,61,.05)',
          pointerEvents: 'none',
        }}
      />

      <div style={{ position: 'relative', zIndex: 1, maxWidth: 800, margin: '0 auto' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 16px',
            borderRadius: 20,
            background: '#EBF4EE',
            border: '1px solid rgba(45,90,61,.2)',
            fontSize: 12,
            fontWeight: 700,
            color: '#2D5A3D',
            marginBottom: '1.5rem',
          }}
        >
          🏆 بیش از ۵۰۰ ادیتور حرفه‌ای تایید شده
        </div>

        <h1
          style={{
            fontSize: 'clamp(28px,5vw,56px)',
            fontWeight: 900,
            lineHeight: 1.2,
            color: '#3D3022',
            marginBottom: '.8rem',
          }}
        >
          بهترین ادیتورها را <span style={{ color: '#2D5A3D' }}>در یک کلیک</span> پیدا کنید
        </h1>

        <p
          style={{
            fontSize: 'clamp(14px,2vw,18px)',
            color: '#5C5C5C',
            lineHeight: 1.8,
            maxWidth: 550,
            margin: '0 auto 2.5rem',
          }}
        >
          ریتاچر، مارکت‌پلیس تخصصی روتوش، ادیت عکس، آتلیه و هوش مصنوعی تصویری.
          کارفرما سفارش بده، ادیتور کار کن، هر دو رشد کنید.
        </p>

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link
            href="/register"
            style={{
              padding: '14px 36px',
              borderRadius: 12,
              background: '#3D3022',
              color: 'white',
              fontSize: 15,
              fontWeight: 700,
              textDecoration: 'none',
              display: 'inline-block',
              boxShadow: '0 4px 16px rgba(92,74,50,.25)',
            }}
          >
            ثبت سفارش رایگان
          </Link>
          <Link
            href="#how"
            style={{
              padding: '14px 36px',
              borderRadius: 12,
              border: '2px solid #2D5A3D',
              color: '#1A3D28',
              fontSize: 15,
              fontWeight: 700,
              textDecoration: 'none',
              display: 'inline-block',
            }}
          >
            ببین چطور کار می‌کند ▶
          </Link>
        </div>

        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '3rem',
            marginTop: '4rem',
            flexWrap: 'wrap',
          }}
        >
          {[
            { num: '+۵۰۰', label: 'ادیتور تایید شده' },
            { num: '+۱۲۰۰۰', label: 'پروژه تکمیل شده' },
            { num: '۴.۹★', label: 'میانگین امتیاز' },
            { num: '۲۴ ساعت', label: 'تحویل سریع' },
          ].map((s) => (
            <div key={s.label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 32, fontWeight: 900, color: '#3D3022' }}>{s.num}</div>
              <div style={{ fontSize: 12, color: '#5C5C5C', marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TrustBar() {
  return (
    <div style={{ background: '#3D3022', padding: '1rem 1.5rem' }}>
      <div
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '3rem',
          flexWrap: 'wrap',
        }}
      >
        {[
          { icon: '🔒', label: 'پرداخت امن' },
          { icon: '✅', label: 'ادیتورهای تایید شده' },
          { icon: '🔄', label: 'ضمانت بازگشت وجه' },
          { icon: '⚡', label: 'تحویل سریع' },
          { icon: '🤝', label: 'پشتیبانی ۲۴/۷' },
        ].map((item) => (
          <div
            key={item.label}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              color: 'rgba(255,255,255,.8)',
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            <span style={{ fontSize: 18 }}>{item.icon}</span>
            {item.label}
          </div>
        ))}
      </div>
    </div>
  );
}

function ServicesSection() {
  const services = [
    {
      icon: '🎨',
      title: 'روتوش عکس',
      desc: 'روتوش حرفه‌ای پرتره، مد، تبلیغات و محصول.',
      tags: ['پرتره', 'مد', 'محصول'],
      accent: '#5C4A32',
    },
    {
      icon: '📸',
      title: 'ادیت و رنگ‌بندی',
      desc: 'Color grading حرفه‌ای، تنظیم نور و رنگ.',
      tags: ['Color Grade', 'LUT', 'Preset'],
      accent: '#2D5A3D',
    },
    {
      icon: '🤖',
      title: 'هوش مصنوعی',
      desc: 'تولید تصویر با AI، Inpainting، Upscaling.',
      tags: ['Midjourney', 'Stable Diffusion', 'AI Fix'],
      accent: '#1E3A5F',
    },
    {
      icon: '🏢',
      title: 'خدمات آتلیه',
      desc: 'ویرایش دسته‌ای عکس‌های آتلیه، تغییر بک‌گراند.',
      tags: ['کودک', 'عروسی', 'تجاری'],
      accent: '#5C4A32',
    },
    {
      icon: '🛍️',
      title: 'عکاسی محصول',
      desc: 'حذف پس‌زمینه، Ghost Mannequin، آماده‌سازی E-commerce.',
      tags: ['بک‌گراند سفید', 'Ghost'],
      accent: '#2D5A3D',
    },
    {
      icon: '🎬',
      title: 'ویدئو و موشن',
      desc: 'ادیت ویدئو، Color Grade، ساخت کلیپ تبلیغاتی.',
      tags: ['Reels', 'TikTok', 'تجاری'],
      accent: '#1E3A5F',
    },
  ];

  return (
    <section id="services" style={{ padding: '5rem 1.5rem' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <SectionHeader
          eyebrow="خدمات ما"
          title="هر نوع خدمات تصویری که نیاز دارید"
          desc="از روتوش ساده تا پروژه‌های سنگین تجاری — ادیتورهای تخصصی ما آماده‌اند"
        />
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))',
            gap: '1.5rem',
          }}
        >
          {services.map((s) => (
            <div
              key={s.title}
              style={{
                background: 'white',
                borderRadius: 16,
                border: '1px solid #EDE5D8',
                padding: '2rem',
                transition: 'all .3s',
                borderRight: `4px solid ${s.accent}`,
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 16px 40px rgba(0,0,0,.08)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = '';
                e.currentTarget.style.boxShadow = '';
              }}
            >
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 14,
                  background: s.accent + '15',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 24,
                  marginBottom: '1.25rem',
                }}
              >
                {s.icon}
              </div>
              <h3
                style={{
                  fontSize: 17,
                  fontWeight: 700,
                  color: '#3D3022',
                  marginBottom: '.5rem',
                }}
              >
                {s.title}
              </h3>
              <p style={{ fontSize: 13, color: '#5C5C5C', lineHeight: 1.8 }}>{s.desc}</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: '1rem' }}>
                {s.tags.map((t) => (
                  <span
                    key={t}
                    style={{
                      padding: '3px 10px',
                      borderRadius: 20,
                      fontSize: 11,
                      fontWeight: 600,
                      background: s.accent + '12',
                      color: s.accent,
                    }}
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    { n: '۱', title: 'سفارش ثبت کنید', desc: 'پروژه خود را با جزئیات توضیح دهید — نوع کار، بودجه، و زمان‌بندی' },
    { n: '۲', title: 'ادیتور انتخاب کنید', desc: 'پیشنهادات ادیتورها را مقایسه کنید و بهترین گزینه را انتخاب کنید' },
    { n: '۳', title: 'کار انجام می‌شود', desc: 'ادیتور در ضرب‌الاجل مشخص کار را تحویل می‌دهد' },
    { n: '۴', title: 'تایید و پرداخت', desc: 'پس از تایید نهایی، وجه به ادیتور پرداخت می‌شود' },
  ];

  return (
    <section id="how" style={{ background: '#F9F5EF', padding: '5rem 1.5rem' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <SectionHeader
          eyebrow="نحوه کار"
          title="در ۴ گام ساده شروع کنید"
          desc="از ثبت سفارش تا تحویل نهایی — فرایند شفاف و مطمئن"
        />
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))',
            gap: '1.5rem',
          }}
        >
          {steps.map((s) => (
            <div key={s.n} style={{ textAlign: 'center', padding: '2rem 1.5rem' }}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  background: '#3D3022',
                  color: 'white',
                  fontSize: 18,
                  fontWeight: 900,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 1.25rem',
                }}
              >
                {s.n}
              </div>
              <h3
                style={{
                  fontSize: 16,
                  fontWeight: 700,
                  color: '#3D3022',
                  marginBottom: '.5rem',
                }}
              >
                {s.title}
              </h3>
              <p style={{ fontSize: 13, color: '#5C5C5C', lineHeight: 1.8 }}>{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function EditorTypesSection() {
  const types = [
    { emoji: '👤', title: 'روتوشر پرتره', desc: 'ویرایش عکس‌های چهره و پوست', count: '+۱۲۰ ادیتور' },
    { emoji: '👗', title: 'ادیتور مد', desc: 'کار با برندهای لباس و اکسسوری', count: '+۸۰ ادیتور' },
    { emoji: '🏠', title: 'معماری', desc: 'ادیت فضای داخلی و دکوراسیون', count: '+۴۵ ادیتور' },
    { emoji: '💒', title: 'عکاسی عروسی', desc: 'ادیت آلبوم عروس و داماد', count: '+۹۰ ادیتور' },
    { emoji: '🍔', title: 'عکاسی غذا', desc: 'ویرایش تصاویر رستوران و کافه', count: '+۳۵ ادیتور' },
  ];

  return (
    <section id="editors" style={{ padding: '5rem 1.5rem' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <SectionHeader eyebrow="تخصص‌ها" title="ادیتورهای تخصصی در هر حوزه‌ای" />
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit,minmax(190px,1fr))',
            gap: '1rem',
          }}
        >
          {types.map((t) => (
            <div
              key={t.title}
              style={{
                background: 'white',
                border: '1px solid #EDE5D8',
                borderRadius: 14,
                padding: '1.75rem 1.5rem',
                textAlign: 'center',
                transition: 'all .25s',
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#2D5A3D';
                e.currentTarget.style.background = '#EBF4EE';
                e.currentTarget.style.transform = 'translateY(-3px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#EDE5D8';
                e.currentTarget.style.background = 'white';
                e.currentTarget.style.transform = '';
              }}
            >
              <span style={{ fontSize: 36, display: 'block', marginBottom: '.75rem' }}>{t.emoji}</span>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#3D3022', marginBottom: '.4rem' }}>
                {t.title}
              </div>
              <div style={{ fontSize: 12, color: '#5C5C5C', lineHeight: 1.7 }}>{t.desc}</div>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#2D5A3D', marginTop: '.75rem' }}>
                {t.count}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function PricingSection() {
  const plans = [
    {
      name: 'کارفرما رایگان',
      price: 'رایگان',
      sub: 'برای همیشه',
      desc: 'برای کسی که می‌خواهد سفارش ثبت کند',
      features: ['ثبت نامحدود پروژه', 'دسترسی به تمام ادیتورها', 'سیستم اسکرو امن', 'پشتیبانی چت'],
      cta: 'شروع کنید',
      featured: false,
    },
    {
      name: 'ادیتور حرفه‌ای',
      price: '۱۰٪',
      sub: 'کمیسیون از درآمد',
      desc: 'برای ادیتورهایی که خدمات ارائه می‌دهند',
      features: ['پروفایل حرفه‌ای', 'نمایش پرتفولیو', 'دریافت پیشنهاد پروژه', 'کیف پول و برداشت', 'امتیازدهی'],
      cta: 'همین الان شروع کن',
      featured: true,
    },
    {
      name: 'آتلیه و استودیو',
      price: 'سفارشی',
      sub: 'تماس بگیرید',
      desc: 'برای تیم‌های بزرگ با حجم کاری بالا',
      features: ['داشبورد تیمی', 'مدیریت چند ادیتور', 'قرارداد سفارشی', 'کمیسیون ویژه'],
      cta: 'تماس با ما',
      featured: false,
    },
  ];

  return (
    <section
      id="pricing"
      style={{
        background: 'linear-gradient(160deg,#E8EFF8 0%,#F9F5EF 100%)',
        padding: '5rem 1.5rem',
      }}
    >
      <div style={{ maxWidth: 1000, margin: '0 auto' }}>
        <SectionHeader
          eyebrow="قیمت‌گذاری"
          title="شفاف، منصفانه، برای همه"
          desc="ریتاچر فقط ۱۰٪ کمیسیون می‌گیرد. بدون هزینه مخفی."
        />
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit,minmax(260px,1fr))',
            gap: '1.5rem',
          }}
        >
          {plans.map((plan) => (
            <div
              key={plan.name}
              style={{
                background: 'white',
                borderRadius: 16,
                padding: '2.5rem 2rem',
                border: plan.featured ? '2px solid #3D3022' : '2px solid #EDE5D8',
                position: 'relative',
              }}
            >
              {plan.featured && (
                <div
                  style={{
                    position: 'absolute',
                    top: -14,
                    right: '50%',
                    transform: 'translateX(50%)',
                    background: '#3D3022',
                    color: 'white',
                    fontSize: 11,
                    fontWeight: 700,
                    padding: '4px 16px',
                    borderRadius: 20,
                    whiteSpace: 'nowrap',
                  }}
                >
                  محبوب‌ترین
                </div>
              )}
              <div style={{ fontSize: 14, fontWeight: 700, color: '#5C5C5C', marginBottom: '.5rem' }}>
                {plan.name}
              </div>
              <div style={{ fontSize: 32, fontWeight: 900, color: '#3D3022' }}>
                {plan.price}{' '}
                <span style={{ fontSize: 14, fontWeight: 500, color: '#5C5C5C' }}>{plan.sub}</span>
              </div>
              <p style={{ fontSize: 13, color: '#5C5C5C', margin: '.75rem 0 1.5rem', lineHeight: 1.7 }}>
                {plan.desc}
              </p>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 2 }}>
                {plan.features.map((f) => (
                  <li
                    key={f}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      fontSize: 13,
                      color: '#5C5C5C',
                      padding: '5px 0',
                      borderBottom: '1px solid #F9F5EF',
                    }}
                  >
                    <span style={{ color: '#2D5A3D', fontWeight: 700 }}>✓</span> {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/register"
                style={{
                  display: 'block',
                  width: '100%',
                  padding: 12,
                  borderRadius: 10,
                  marginTop: '1.5rem',
                  textAlign: 'center',
                  fontSize: 14,
                  fontWeight: 700,
                  textDecoration: 'none',
                  ...(plan.featured
                    ? { background: '#3D3022', color: 'white' }
                    : { border: '2px solid #3D3022', color: '#3D3022', background: 'transparent' }),
                }}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TestimonialsSection() {
  const items = [
    {
      text: 'ریتاچر زندگیم رو تغییر داد. الان ماهانه ۱۵ میلیون درآمد دارم از همین پلتفرم.',
      name: 'امیر رضایی',
      role: 'روتوشر حرفه‌ای',
      color: '#2D5A3D',
      initial: 'ا',
    },
    {
      text: 'برای آتلیه‌ام عالیه. سیستم امن و پشتیبانی سریع.',
      name: 'نرگس محمدی',
      role: 'مدیر آتلیه',
      color: '#5C4A32',
      initial: 'ن',
    },
    {
      text: 'سیستم اسکرو خیلی مطمئنه. این اعتماد ایجاد می‌کنه برای هر دو طرف.',
      name: 'سینا کریمی',
      role: 'عکاس تجاری',
      color: '#1E3A5F',
      initial: 'س',
    },
  ];

  return (
    <section style={{ padding: '5rem 1.5rem' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <SectionHeader eyebrow="نظرات کاربران" title="آنچه کاربران می‌گویند" />
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))',
            gap: '1.5rem',
          }}
        >
          {items.map((item) => (
            <div
              key={item.name}
              style={{
                background: '#F9F5EF',
                borderRadius: 16,
                padding: '2rem',
                border: '1px solid #EDE5D8',
              }}
            >
              <div style={{ fontSize: 28, color: '#5C4A32', marginBottom: '1rem' }}>"</div>
              <p style={{ fontSize: 14, color: '#5C5C5C', lineHeight: 1.9, marginBottom: '1.5rem' }}>
                {item.text}
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: '50%',
                    background: item.color,
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                  }}
                >
                  {item.initial}
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#3D3022' }}>{item.name}</div>
                  <div style={{ fontSize: 12, color: '#9A9A9A' }}>{item.role}</div>
                  <div style={{ color: '#F0B429', fontSize: 13 }}>★★★★★</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  return (
    <section
      style={{
        background: 'linear-gradient(135deg,#3D3022 0%,#1A3D28 100%)',
        padding: '5rem 1.5rem',
        textAlign: 'center',
      }}
    >
      <h2
        style={{
          fontSize: 'clamp(22px,4vw,40px)',
          fontWeight: 900,
          color: 'white',
          marginBottom: '1rem',
        }}
      >
        آماده‌اید شروع کنید؟
      </h2>
      <p
        style={{
          fontSize: 15,
          color: 'rgba(255,255,255,.75)',
          maxWidth: 500,
          margin: '0 auto 2.5rem',
          lineHeight: 1.8,
        }}
      >
        به جمع هزاران کارفرما و ادیتور حرفه‌ای ریتاچر بپیوندید.
      </p>
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link
          href="/register?role=client"
          style={{
            padding: '14px 32px',
            borderRadius: 12,
            background: 'white',
            color: '#3D3022',
            fontSize: 15,
            fontWeight: 700,
            textDecoration: 'none',
          }}
        >
          کارفرما هستم — سفارش ثبت کنم
        </Link>
        <Link
          href="/register?role=editor"
          style={{
            padding: '14px 32px',
            borderRadius: 12,
            border: '2px solid rgba(255,255,255,.5)',
            color: 'white',
            fontSize: 15,
            fontWeight: 700,
            textDecoration: 'none',
          }}
        >
          ادیتور هستم — پروفایل بسازم
        </Link>
      </div>
    </section>
  );
}

function SectionHeader({
  eyebrow,
  title,
  desc,
}: {
  eyebrow: string;
  title: string;
  desc?: string;
}) {
  return (
    <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
      <span
        style={{
          display: 'inline-block',
          fontSize: 12,
          fontWeight: 700,
          color: '#2D5A3D',
          textTransform: 'uppercase',
          letterSpacing: '.1em',
          marginBottom: '.75rem',
        }}
      >
        {eyebrow}
      </span>
      <h2
        style={{
          fontSize: 'clamp(22px,3.5vw,36px)',
          fontWeight: 900,
          color: '#3D3022',
          marginBottom: '.75rem',
        }}
      >
        {title}
      </h2>
      {desc && (
        <p style={{ fontSize: 15, color: '#5C5C5C', maxWidth: 500, margin: '0 auto', lineHeight: 1.8 }}>
          {desc}
        </p>
      )}
    </div>
  );
}
```


## src\lib\api\auth.ts

```tsx
import { apiClient } from './client';
import type { User } from '@/types';

export type BackendUserRole = 'client' | 'editor';
export type UiUserRole = 'client' | 'editor' | 'studio' | 'atelier';
export type UserRole = UiUserRole;

export type AuthUser = User;

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
  phone_number?: string;
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

function normalizeBackendRole(role: UiUserRole): BackendUserRole {
  if (role === 'editor') return 'editor';

  // Backend currently supports only client/editor.
  // studio/atelier are temporarily registered as client.
  return 'client';
}

function getAccessToken(data: AuthResponse): string | null {
  return data.access || data.access_token || data.token || null;
}

function getRefreshToken(data: AuthResponse): string | null {
  return data.refresh || data.refresh_token || null;
}

function normalizeUser(data: unknown): User {
  const raw =
    data !== null && typeof data === 'object'
      ? (data as Record<string, unknown>)
      : {};

  return {
    id: Number(raw.id || 0),
    username: String(raw.username || ''),
    email: typeof raw.email === 'string' ? raw.email : null,

    phone_number:
      typeof raw.phone_number === 'string'
        ? raw.phone_number
        : typeof raw.phone === 'string'
          ? raw.phone
          : null,

    first_name:
      typeof raw.first_name === 'string'
        ? raw.first_name
        : '',

    last_name:
      typeof raw.last_name === 'string'
        ? raw.last_name
        : '',

    role:
      typeof raw.role === 'string'
        ? raw.role
        : 'client',

    is_verified:
      typeof raw.is_verified === 'boolean'
        ? raw.is_verified
        : false,

    avatar:
      typeof raw.avatar === 'string'
        ? raw.avatar
        : undefined,

    date_joined:
      typeof raw.date_joined === 'string'
        ? raw.date_joined
        : typeof raw.created_at === 'string'
          ? raw.created_at
          : new Date().toISOString(),
  };
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
      user?: User | null;
      isAuthenticated?: boolean;
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

  if (data.user) {
    parsed.state.user = normalizeUser(data.user);
  }

  parsed.state.isAuthenticated = Boolean(parsed.state.accessToken);

  localStorage.setItem('retoucher-auth', JSON.stringify(parsed));

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
    localStorage.setItem('user', JSON.stringify(normalizeUser(data.user)));
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
      phone_number: payload.phone_number || payload.phone || '',
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

    const { data } = await apiClient.post('/api/auth/token/', body);

    saveAuthSession(data);

    return data;
  },

  me: async (): Promise<User> => {
    const { data } = await apiClient.get('/api/accounts/me/');
    return normalizeUser(data);
  },

  getMe: async (): Promise<User> => {
    const { data } = await apiClient.get('/api/accounts/me/');
    return normalizeUser(data);
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


## src\lib\api\catalog.ts

```tsx
import { apiClient } from './client';
import type { EditCategory, EditStyle } from '@/types';

export const catalogAPI = {
  categories: async (): Promise<EditCategory[]> => {
    const { data } = await apiClient.get('/api/catalog/categories/');
    return data;
  },

  styles: async (categoryId?: number): Promise<EditStyle[]> => {
    const params = categoryId ? { category: String(categoryId) } : {};
    const { data } = await apiClient.get('/api/catalog/styles/', { params });
    return data;
  },
};
```


## src\lib\api\client.ts

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


## src\lib\api\editors.ts

```tsx
import { apiClient } from './client';

export interface EditorSkill {
  id: number;
  category: number;
  category_title: string;
  title: string;
  slug: string;
  description: string;
  min_price: number;
  max_price: number;
  suggested_price: number;
  estimated_delivery_hours: number;
  packages: unknown[];
}

export interface EditorPortfolioItem {
  id: number;
  title: string;
  description: string;
  style: number | null;
  style_title: string;
  before_image: string | null;
  after_image: string | null;
  is_featured: boolean;
}

export interface EditorProfile {
  id: number;
  user: number;
  username: string;
  display_name: string;
  bio: string;
  level: 'junior' | 'mid' | 'senior' | 'pro';
  skills: EditorSkill[];
  base_price: number;
  average_delivery_hours: number;
  rating_average: string | number;
  completed_orders_count: number;
  is_available: boolean;
  accepts_direct_requests: boolean;
  accepts_public_requests: boolean;
  accepts_sample_challenges: boolean;
  portfolio_items?: EditorPortfolioItem[];
}

export const editorsAPI = {
  list: async (params?: Record<string, string | number | boolean>) => {
    const { data } = await apiClient.get('/api/accounts/editors/', { params });
    return Array.isArray(data) ? data : data.results ?? [];
  },

  get: async (id: number | string) => {
    const { data } = await apiClient.get(`/api/accounts/editors/${id}/`);
    return data as EditorProfile;
  },
};
```


## src\lib\api\endpoints.ts

```tsx
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
```


## src\lib\api\orders.ts

```tsx
import { apiClient } from './client';
import type {
  Order,
  OrderComment,
  OrderImage,
  PaginatedResponse,
  OrderActivityLog,
  OrderStatusHistory,
} from '@/types';

type MaybePaginated<T> = PaginatedResponse<T> | T[];

function normalizeList<T>(data: MaybePaginated<T>): PaginatedResponse<T> {
  if (Array.isArray(data)) {
    return {
      count: data.length,
      next: null,
      previous: null,
      results: data,
    };
  }

  return data;
}

export type CreateOrderPayload = {
  title: string;
  description?: string;
  deadline?: string | null;
};

export type UpdateOrderPayload = Partial<CreateOrderPayload>;

export type CreateCommentPayload = {
  target_type?: 'order' | 'image' | 'delivery' | 'revision';
  image?: number | null;
  delivery?: number | null;
  revision?: number | null;
  text?: string;
  x?: number | null;
  y?: number | null;
  parent?: number | null;
  annotation_type?: 'none' | 'point' | 'rectangle' | 'circle' | 'arrow' | 'freehand';
  annotation_label?: string;
  annotation_color?: string;
  annotation_data?: Record<string, unknown>;
};

export type UpdateCommentPayload = Partial<CreateCommentPayload>;

export const ordersAPI = {
  list: async (
    params?: Record<string, string | number | boolean>
  ): Promise<PaginatedResponse<Order>> => {
    const { data } = await apiClient.get('/api/orders/', { params });
    return normalizeList<Order>(data);
  },

  get: async (id: number | string): Promise<Order> => {
    const { data } = await apiClient.get(`/api/orders/${id}/`);
    return data;
  },

  create: async (payload: CreateOrderPayload): Promise<Order> => {
    const { data } = await apiClient.post('/api/orders/', payload);
    return data;
  },

  update: async (id: number | string, payload: UpdateOrderPayload): Promise<Order> => {
    const { data } = await apiClient.patch(`/api/orders/${id}/`, payload);
    return data;
  },

  remove: async (id: number | string): Promise<void> => {
    await apiClient.delete(`/api/orders/${id}/`);
  },

  submit: async (id: number | string): Promise<Order> => {
    const { data } = await apiClient.post(`/api/orders/${id}/submit/`);
    return data;
  },

  approve: async (id: number | string): Promise<Order> => {
    const { data } = await apiClient.post(`/api/orders/${id}/client-approve/`);
    return data;
  },

  requestRevision: async (id: number | string, note: string): Promise<Order> => {
    const { data } = await apiClient.post(`/api/orders/${id}/client-request-revision/`, {
      note,
    });
    return data;
  },

  rate: async (id: number | string, score: number, comment = ''): Promise<Order | void> => {
    const { data } = await apiClient.post(`/api/orders/${id}/client-rate/`, {
      score,
      comment,
    });
    return data;
  },

  uploadImage: async (
    id: number | string,
    file: File,
    note = ''
  ): Promise<OrderImage> => {
    const formData = new FormData();
    formData.append('image', file);
    if (note) {
      formData.append('note', note);
    }

    const { data } = await apiClient.post(`/api/orders/${id}/upload-image/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return data;
  },

  getComments: async (id: number | string): Promise<OrderComment[]> => {
    const { data } = await apiClient.get(`/api/orders/${id}/comments/`);
    return Array.isArray(data) ? data : data.results ?? [];
  },

  getCommentThreads: async (id: number | string): Promise<OrderComment[]> => {
    const { data } = await apiClient.get(`/api/orders/${id}/comment-threads/`);
    return Array.isArray(data) ? data : data.results ?? [];
  },

  createComment: async (
    id: number | string,
    payload: CreateCommentPayload
  ): Promise<OrderComment> => {
    const { data } = await apiClient.post(`/api/orders/${id}/comments/`, payload);
    return data;
  },

  updateComment: async (
    id: number | string,
    commentId: number | string,
    payload: UpdateCommentPayload
  ): Promise<OrderComment> => {
    const { data } = await apiClient.patch(
      `/api/orders/${id}/comments/${commentId}/`,
      payload
    );
    return data;
  },

  resolveComment: async (
    id: number | string,
    commentId: number | string
  ): Promise<OrderComment> => {
    const { data } = await apiClient.post(
      `/api/orders/${id}/comments/${commentId}/resolve/`
    );
    return data;
  },

  unresolveComment: async (
    id: number | string,
    commentId: number | string
  ): Promise<OrderComment> => {
    const { data } = await apiClient.post(
      `/api/orders/${id}/comments/${commentId}/unresolve/`
    );
    return data;
  },

  setCommentStatus: async (
    id: number | string,
    commentId: number | string,
    status: 'active' | 'resolved' | 'approved' | 'deleted'
  ): Promise<OrderComment> => {
    const { data } = await apiClient.post(
      `/api/orders/${id}/comments/${commentId}/set-status/`,
      { status }
    );
    return data;
  },

  getActivityLog: async (id: number | string): Promise<OrderActivityLog[]> => {
    const { data } = await apiClient.get(`/api/orders/${id}/activity-log/`);
    return Array.isArray(data) ? data : data.results ?? [];
  },

  getStatusHistory: async (id: number | string): Promise<OrderStatusHistory[]> => {
    const { data } = await apiClient.get(`/api/orders/${id}/status-history/`);
    return Array.isArray(data) ? data : data.results ?? [];
  },
};
```


## src\lib\api\payments.ts

```tsx
```


## src\lib\api\projects.ts

```tsx
import { apiClient } from './client';
import type { ProjectRequest, CreateProjectPayload, PaginatedResponse } from '@/types';

export const projectsAPI = {
  list: async (params?: Record<string, string>): Promise<PaginatedResponse<ProjectRequest>> => {
    const { data } = await apiClient.get('/api/projects/requests/', { params });
    return data;
  },

  get: async (id: number): Promise<ProjectRequest> => {
    const { data } = await apiClient.get(`/api/projects/requests/${id}/`);
    return data;
  },

  create: async (payload: CreateProjectPayload): Promise<ProjectRequest> => {
    const { data } = await apiClient.post('/api/projects/requests/', payload);
    return data;
  },

  submit: async (id: number): Promise<ProjectRequest> => {
    const { data } = await apiClient.post(`/api/projects/requests/${id}/submit/`);
    return data;
  },

  uploadImage: async (projectId: number, file: File, caption?: string): Promise<void> => {
    const form = new FormData();
    form.append('image', file);
    if (caption) form.append('caption', caption);
    await apiClient.post(`/api/projects/requests/${projectId}/upload-image/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/projects/requests/${id}/`);
  },
};
```


## src\lib\stores\auth.store.ts

```tsx
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  // Actions
  setAuth: (user: User, access: string, refresh: string) => void;
  clearAuth: () => void;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setAuth: (user, access, refresh) =>
        set({ user, accessToken: access, refreshToken: refresh, isAuthenticated: true }),

      clearAuth: () =>
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false }),

      setUser: (user) => set({ user }),
    }),
    {
      name: 'retoucher-auth',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Helpers
export const useUser = () => useAuthStore((s) => s.user);
export const useIsAuthenticated = () => useAuthStore((s) => s.isAuthenticated);
export const useUserRole = () => useAuthStore((s) => s.user?.role);
```


## src\styles\auth.css

```tsx
:root {
  --rt-rose: #F2A8C4;
  --rt-rose-deep: #E07AA0;
  --rt-rose-light: #FDF0F6;
  --rt-lavender: #C4B5F4;
  --rt-lavender-deep: #9B85E8;
  --rt-lavender-light: #F3F0FE;
  --rt-sage: #A8D5C2;
  --rt-sage-deep: #6DB89A;
  --rt-sage-light: #EEF8F4;
  --rt-peach: #F4C4A8;
  --rt-peach-deep: #E89B6D;
  --rt-peach-light: #FEF5F0;
  --rt-sky: #A8C4F4;
  --rt-sky-deep: #6D9BE8;
  --rt-sky-light: #F0F5FE;
}

.auth-gradient-bg {
  background: linear-gradient(145deg, #FDF0F6 0%, #F3F0FE 40%, #EEF8F4 100%);
}

.auth-card {
  background: white;
  border-radius: 20px;
  border: 1px solid #EBEBF0;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}

.btn-auth-primary {
  background: linear-gradient(135deg, var(--rt-lavender) 0%, var(--rt-rose) 100%);
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-auth-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(196, 181, 244, 0.4);
}

.input-auth {
  border: 1.5px solid #EBEBF0;
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
}

.input-auth:focus {
  border-color: var(--rt-lavender);
  background: var(--rt-lavender-light);
  box-shadow: 0 0 0 3px rgba(196, 181, 244, 0.15);
}

.otp-input {
  border: 1.5px solid #EBEBF0;
  transition: all 0.2s;
}

.otp-input:focus {
  border-color: var(--rt-lavender);
  background: var(--rt-lavender-light);
  box-shadow: 0 0 0 3px rgba(196, 181, 244, 0.15);
}

.otp-input.filled {
  border-color: var(--rt-lavender);
  background: var(--rt-lavender-light);
  color: var(--rt-lavender-deep);
}

.role-card {
  border: 1.5px solid #EBEBF0;
  transition: all 0.2s;
}

.role-card:hover {
  border-color: var(--rt-lavender);
  background: var(--rt-lavender-light);
}

.role-card.selected {
  border-color: var(--rt-lavender-deep);
  background: var(--rt-lavender-light);
}

.strength-bar-fill {
  transition: width 0.4s, background 0.4s;
}
```


## src\types\index.ts

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
