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