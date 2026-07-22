'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { authAPI } from '@/lib/api/auth';
import { getApiErrorMessage } from '@/lib/api/client';
import { useAuthStore } from '@/lib/stores/auth.store';

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();

  const [form, setForm] = useState({ username: '', password: '' });
  const [showPass, setShowPass] = useState(false);
  const [remember, setRemember] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isValid = form.username.trim().length >= 3 && form.password.length >= 6;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;
    setLoading(true);
    setError('');
    try {
      const data = await authAPI.login({ username: form.username.trim(), password: form.password });
      const me = await authAPI.getMe();
      setAuth(me, data.access, data.refresh);
      router.push('/dashboard');
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'نام کاربری یا رمز عبور اشتباه است.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      <div
        className="hidden lg:flex flex-1 flex-col items-center justify-center p-12 relative overflow-hidden"
        style={{ background: 'linear-gradient(145deg,#FDF0F6 0%,#F3F0FE 40%,#EEF8F4 100%)' }}
      >
        <div className="absolute -top-20 -right-20 w-72 h-72 rounded-full" style={{ background: 'rgba(196,181,244,.2)' }} />
        <div className="absolute -bottom-16 -left-16 w-56 h-56 rounded-full" style={{ background: 'rgba(168,213,194,.2)' }} />
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
              <span key={b.label} className="px-4 py-1.5 rounded-full text-sm font-medium" style={{ background: b.bg, color: b.color }}>
                {b.label}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 lg:max-w-md flex items-center justify-center px-8 py-12" style={{ background: 'white' }}>
        <form onSubmit={handleSubmit} className="w-full max-w-sm">
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-8 h-8 rounded-xl flex items-center justify-center text-base" style={{ background: 'linear-gradient(135deg,#F2A8C4,#C4B5F4)' }}>
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
              <label className="block text-sm font-medium text-gray-700 mb-1.5">نام کاربری</label>
              <input
                type="text"
                autoComplete="username"
                value={form.username}
                onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                placeholder="نام کاربری"
                className="input-auth w-full px-4 py-3 rounded-xl text-sm bg-gray-50 outline-none"
                style={{ fontFamily: 'inherit' }}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">رمز عبور</label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={form.password}
                  onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                  placeholder="حداقل ۸ کاراکتر"
                  className="input-auth w-full px-4 py-3 rounded-xl text-sm bg-gray-50 outline-none pr-10"
                  style={{ fontFamily: 'inherit' }}
                />
                <button type="button" onClick={() => setShowPass(!showPass)} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                  {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between mt-4 mb-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="rounded" />
              <span className="text-sm" style={{ color: '#7B7B90' }}>مرا به خاطر بسپار</span>
            </label>
            <Link href="/forgot-password" className="text-sm font-medium" style={{ color: '#9B85E8' }}>
              فراموش کردید؟
            </Link>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl text-sm" style={{ background: '#FEF5F0', color: '#E89B6D', border: '1px solid rgba(232,155,109,.3)' }}>
              {error}
            </div>
          )}

          <button type="submit" disabled={!isValid || loading} className="btn-auth-primary w-full py-3 rounded-xl text-white font-semibold text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
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
              <button key={s.label} type="button" className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium border transition-colors hover:bg-gray-50" style={{ borderColor: '#EBEBF0', color: '#2D2D3A', fontFamily: 'inherit' }}>
                <span>{s.icon}</span> {s.label}
              </button>
            ))}
          </div>
        </form>
      </div>
    </div>
  );
}
