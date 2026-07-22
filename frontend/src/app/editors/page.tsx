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