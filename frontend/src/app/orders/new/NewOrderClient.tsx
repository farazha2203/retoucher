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