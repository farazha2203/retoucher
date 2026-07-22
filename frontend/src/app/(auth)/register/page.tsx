'use client';

import { FormEvent, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { authAPI } from '@/lib/api/auth';
import { useAuthStore } from '@/lib/stores/auth.store';
import type { UserRole } from '@/types';

type PublicRole = Extract<UserRole, 'client' | 'editor'>;

const roles: Array<{
  id: PublicRole;
  icon: string;
  name: string;
  description: string;
}> = [
  {
    id: 'client',
    icon: '🎨',
    name: 'کارفرما',
    description: 'ثبت سفارش و مدیریت پروژه‌های ادیت',
  },
  {
    id: 'editor',
    icon: '📸',
    name: 'ادیتور',
    description: 'دریافت پروژه و ارائه خدمات تخصصی',
  },
];

function extractApiError(error: unknown): string {
  if (!error || typeof error !== 'object' || !('response' in error)) {
    return 'ثبت‌نام انجام نشد. دوباره تلاش کنید.';
  }

  const response = (error as {
    response?: { data?: Record<string, unknown> | string };
  }).response;
  const data = response?.data;

  if (typeof data === 'string') return data;
  if (!data || typeof data !== 'object') {
    return 'ثبت‌نام انجام نشد. اطلاعات را بررسی کنید.';
  }

  return Object.entries(data)
    .flatMap(([field, value]) => {
      const messages = Array.isArray(value) ? value : [value];
      return messages.map((message) => `${field}: ${String(message)}`);
    })
    .join(' | ');
}

export default function RegisterPage() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [role, setRole] = useState<PublicRole>('client');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isValid = useMemo(
    () =>
      email.includes('@') &&
      password.length >= 8 &&
      password === passwordConfirm,
    [email, password, passwordConfirm]
  );

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!isValid || loading) return;

    setLoading(true);
    setError('');

    try {
      const normalizedEmail = email.trim().toLowerCase();

      await authAPI.register({
        username: normalizedEmail,
        email: normalizedEmail,
        password,
        password_confirm: passwordConfirm,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        phone_number: phoneNumber.trim(),
        role,
      });

      const tokens = await authAPI.login({
        username: normalizedEmail,
        password,
      });
      const user = await authAPI.getMe();
      setAuth(user, tokens.access, tokens.refresh);
      router.replace('/dashboard/orders');
    } catch (registrationError) {
      setError(extractApiError(registrationError));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main
      className="min-h-screen px-4 py-12"
      style={{
        background:
          'linear-gradient(160deg,#FAFAFA 0%,#F3F0FE 50%,#FDF0F6 100%)',
      }}
    >
      <form
        onSubmit={handleSubmit}
        className="auth-card mx-auto w-full max-w-xl p-7 md:p-9"
      >
        <Link
          href="/"
          className="text-sm font-medium"
          style={{ color: '#9B85E8' }}
        >
          بازگشت به خانه
        </Link>

        <h1 className="mt-5 text-2xl font-semibold text-gray-800">
          ساخت حساب ریتاچر
        </h1>
        <p className="mt-2 text-sm text-gray-500">
          در این مرحله فقط حساب کارفرما و ادیتور قابل ثبت است. حساب آتلیه بعداً
          به‌صورت سازمانی پیاده‌سازی می‌شود.
        </p>

        <div className="mt-7 grid grid-cols-2 gap-3">
          {roles.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setRole(item.id)}
              className={`role-card rounded-xl p-4 text-right ${
                role === item.id ? 'selected' : ''
              }`}
            >
              <span className="text-2xl">{item.icon}</span>
              <div className="mt-2 font-semibold text-gray-800">{item.name}</div>
              <div className="mt-1 text-xs leading-5 text-gray-500">
                {item.description}
              </div>
            </button>
          ))}
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <AuthField
            label="نام"
            value={firstName}
            onChange={setFirstName}
            autoComplete="given-name"
          />
          <AuthField
            label="نام خانوادگی"
            value={lastName}
            onChange={setLastName}
            autoComplete="family-name"
          />
          <AuthField
            label="ایمیل"
            type="email"
            value={email}
            onChange={setEmail}
            autoComplete="email"
            required
          />
          <AuthField
            label="شماره تماس"
            value={phoneNumber}
            onChange={setPhoneNumber}
            autoComplete="tel"
          />
          <AuthField
            label="رمز عبور"
            type="password"
            value={password}
            onChange={setPassword}
            autoComplete="new-password"
            placeholder="حداقل ۸ کاراکتر"
            required
          />
          <AuthField
            label="تکرار رمز عبور"
            type="password"
            value={passwordConfirm}
            onChange={setPasswordConfirm}
            autoComplete="new-password"
            required
          />
        </div>

        {passwordConfirm && password !== passwordConfirm && (
          <p className="mt-3 text-sm text-red-600">
            رمز عبور و تکرار آن یکسان نیستند.
          </p>
        )}

        {error && (
          <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={!isValid || loading}
          className="btn-auth-primary mt-6 flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading && <Loader2 size={18} className="animate-spin" />}
          {loading ? 'در حال ساخت حساب...' : 'ثبت‌نام'}
        </button>

        <p className="mt-5 text-center text-sm text-gray-500">
          قبلاً ثبت‌نام کرده‌اید؟{' '}
          <Link href="/login" className="font-medium" style={{ color: '#9B85E8' }}>
            ورود
          </Link>
        </p>
      </form>
    </main>
  );
}

type AuthFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: 'text' | 'email' | 'password';
  autoComplete?: string;
  placeholder?: string;
  required?: boolean;
};

function AuthField({
  label,
  value,
  onChange,
  type = 'text',
  autoComplete,
  placeholder,
  required = false,
}: AuthFieldProps) {
  return (
    <label className="block text-sm font-medium text-gray-700">
      {label}
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        autoComplete={autoComplete}
        placeholder={placeholder}
        required={required}
        className="input-auth mt-1.5 w-full rounded-xl bg-gray-50 px-4 py-3 text-sm outline-none"
      />
    </label>
  );
}
