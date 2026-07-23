 'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Eye,
  EyeOff,
  ImageIcon,
  Loader2,
  ShieldCheck,
  Sparkles,
  WandSparkles,
} from 'lucide-react';

import { GoogleAuthButton } from '@/components/auth/GoogleAuthButton';
import { authAPI } from '@/lib/api/auth';
import { getApiErrorMessage } from '@/lib/api/client';
import { useAuthStore } from '@/lib/stores/auth.store';

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [form, setForm] = useState({ username: '', password: '' });
  const [showPass, setShowPass] = useState(false);
  const [remember, setRemember] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isValid =
    form.username.trim().length >= 3 && form.password.length >= 6;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!isValid) return;

    setLoading(true);
    setError('');

    try {
      const tokens = await authAPI.login({
        username: form.username.trim(),
        password: form.password,
      });
      const user = await authAPI.getMe();
      setAuth(user, tokens.access, tokens.refresh);

      if (
        ['admin', 'support', 'supervisor'].includes(user.role)
      ) {
        const djangoBase =
          process.env.NEXT_PUBLIC_DJANGO_BASE_URL ??
          'http://127.0.0.1:8000';
        window.location.assign(`${djangoBase}/panel/`);
        return;
      }

      router.push('/dashboard');
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          'نام کاربری یا رمز عبور اشتباه است.',
        ),
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main
      dir="rtl"
      className="min-h-screen bg-[#fbf9fd] lg:grid lg:grid-cols-[430px_1fr]"
    >
      <section className="flex min-h-screen items-center justify-center bg-white px-5 py-10 sm:px-10 lg:order-1">
        <form
          onSubmit={handleSubmit}
          className="w-full max-w-sm rounded-[32px] border border-[#eee9f3] bg-white p-2"
        >
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-[#f2a8c4] to-[#9b85e8] text-xl text-white shadow-lg shadow-purple-200/50">
              ✦
            </div>
            <div>
              <strong className="block text-lg text-[#2f2940]">
                ریتاچر
              </strong>
              <span className="text-xs text-[#8e879b]">
                پنل تخصصی مشتریان و ادیتورها
              </span>
            </div>
          </div>

          <h1 className="text-3xl font-black text-[#2d2738]">
            خوش برگشتی
          </h1>
          <p className="mt-2 text-sm leading-7 text-[#81798c]">
            سفارش‌ها، پروژه‌ها، نمونه‌ها و درآمد خودت را از یک پنل
            یکپارچه مدیریت کن.
          </p>

          <div className="mt-7">
            <GoogleAuthButton label="ورود یا عضویت با گوگل" />
          </div>

          <div className="my-6 flex items-center gap-3">
            <div className="h-px flex-1 bg-[#eeeaf2]" />
            <span className="text-xs text-[#aaa2b3]">
              یا ورود با رمز
            </span>
            <div className="h-px flex-1 bg-[#eeeaf2]" />
          </div>

          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-bold text-[#51495d]">
                نام کاربری یا ایمیل
              </label>
              <input
                type="text"
                autoComplete="username"
                value={form.username}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    username: event.target.value,
                  }))
                }
                placeholder="ایمیل یا نام کاربری"
                className="w-full rounded-2xl border border-[#ebe6ef] bg-[#faf9fc] px-4 py-3.5 text-sm outline-none transition focus:border-[#ad91e8] focus:bg-white focus:ring-4 focus:ring-[#ad91e8]/10"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-bold text-[#51495d]">
                رمز عبور
              </label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={form.password}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      password: event.target.value,
                    }))
                  }
                  placeholder="حداقل ۶ کاراکتر"
                  className="w-full rounded-2xl border border-[#ebe6ef] bg-[#faf9fc] px-4 py-3.5 pl-12 text-sm outline-none transition focus:border-[#ad91e8] focus:bg-white focus:ring-4 focus:ring-[#ad91e8]/10"
                />
                <button
                  type="button"
                  onClick={() => setShowPass((value) => !value)}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-[#948ba0]"
                  aria-label="نمایش رمز"
                >
                  {showPass ? <EyeOff size={19} /> : <Eye size={19} />}
                </button>
              </div>
            </div>
          </div>

          <div className="my-5 flex items-center justify-between">
            <label className="flex cursor-pointer items-center gap-2 text-sm text-[#70687b]">
              <input
                type="checkbox"
                checked={remember}
                onChange={(event) => setRemember(event.target.checked)}
                className="h-4 w-4 rounded accent-[#9b85e8]"
              />
              مرا به خاطر بسپار
            </label>
            <Link
              href="/forgot-password"
              className="text-sm font-bold text-[#967ce0]"
            >
              بازیابی رمز
            </Link>
          </div>

          {error && (
            <div className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm leading-6 text-rose-700">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={!isValid || loading}
            className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-l from-[#e27da3] to-[#9178dd] px-4 py-3.5 text-sm font-black text-white shadow-xl shadow-purple-200/40 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading && <Loader2 size={18} className="animate-spin" />}
            {loading ? 'در حال ورود...' : 'ورود به پنل'}
          </button>

          <p className="mt-7 text-center text-sm text-[#81798c]">
            هنوز حساب نداری؟{' '}
            <Link href="/register" className="font-black text-[#967ce0]">
              عضویت رایگان
            </Link>
          </p>
        </form>
      </section>

      <section className="relative hidden min-h-screen overflow-hidden bg-gradient-to-br from-[#faeaf2] via-[#f1ecfc] to-[#eaf7f1] p-12 lg:order-2 lg:flex lg:items-center lg:justify-center">
        <div className="absolute -right-24 -top-24 h-96 w-96 rounded-full bg-[#d8c8f5]/35 blur-3xl" />
        <div className="absolute -bottom-24 -left-24 h-80 w-80 rounded-full bg-[#a9d8c3]/35 blur-3xl" />

        <div className="relative z-10 max-w-2xl">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/60 px-4 py-2 text-sm font-bold text-[#6d5c83] shadow-sm backdrop-blur">
            <Sparkles size={16} />
            فضای حرفه‌ای خلاقان تصویر
          </span>

          <h2 className="mt-7 text-5xl font-black leading-[1.35] text-[#332d3d]">
            همه ابزارهای یک ادیتور حرفه‌ای،
            <span className="block bg-gradient-to-l from-[#d86d98] to-[#8269d2] bg-clip-text text-transparent">
              در یک پنل زیبا
            </span>
          </h2>

          <p className="mt-6 max-w-xl text-base leading-9 text-[#766d80]">
            نمونه‌کارها، چالش‌های ادیت، سفارش‌ها، تحویل‌ها، اصلاحات،
            کیف پول و ارتباط با مشتری را یکجا مدیریت کن.
          </p>

          <div className="mt-9 grid grid-cols-3 gap-4">
            {[
              {
                icon: WandSparkles,
                title: 'Workflow حرفه‌ای',
                text: 'روند شفاف از دریافت تا تحویل',
              },
              {
                icon: ImageIcon,
                title: 'نمونه و پورتفولیو',
                text: 'Before / After و چالش نمونه',
              },
              {
                icon: ShieldCheck,
                title: 'پرداخت امن',
                text: 'کیف پول، امانت و تسویه',
              },
            ].map(({ icon: Icon, title, text }) => (
              <article
                key={title}
                className="rounded-3xl border border-white/70 bg-white/55 p-5 shadow-sm backdrop-blur"
              >
                <Icon className="text-[#967ce0]" size={24} />
                <strong className="mt-4 block text-sm text-[#463d50]">
                  {title}
                </strong>
                <p className="mt-2 text-xs leading-6 text-[#84798c]">
                  {text}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
