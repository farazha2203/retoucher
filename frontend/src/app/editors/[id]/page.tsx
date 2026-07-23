'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { editorsAPI, type EditorProfile, type EditorSkill } from '@/lib/api/editors';

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

function getSkillLabel(skill: EditorSkill) {
  return skill.title;
}

export default function EditorDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;

  const [editor, setEditor] = useState<EditorProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;

    let mounted = true;

    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await editorsAPI.get(id);
        if (mounted) setEditor(data);
      } catch {
        if (mounted) setError('دریافت اطلاعات ادیتور با خطا مواجه شد.');
      } finally {
        if (mounted) setLoading(false);
      }
    };

    load();

    return () => {
      mounted = false;
    };
  }, [id]);

  return (
    <main
      className="min-h-screen px-4 py-10"
      style={{ background: 'linear-gradient(160deg,#FAFAFA 0%,#F3F0FE 50%,#FDF0F6 100%)' }}
    >
      <div className="mx-auto max-w-5xl">
        <div className="mb-6">
          <Link href="/editors" className="text-sm font-medium text-violet-700 hover:text-violet-800">
            ← بازگشت به لیست ادیتورها
          </Link>
        </div>

        {loading && (
          <div className="rounded-3xl bg-white p-8 text-center shadow-sm">
            <p className="text-sm text-gray-500">در حال دریافت اطلاعات ادیتور...</p>
          </div>
        )}

        {!loading && error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-center text-sm text-red-600">
            {error}
          </div>
        )}

        {!loading && !error && editor && (
          <section className="rounded-3xl bg-white p-8 shadow-sm">
            <div className="flex flex-col gap-6 md:flex-row md:items-start">
              <div className="shrink-0">
                <div className="flex h-28 w-28 items-center justify-center rounded-3xl bg-violet-100 text-4xl font-bold text-violet-700">
                  {getEditorName(editor).charAt(0)}
                </div>
              </div>

              <div className="flex-1">
                <h1 className="text-3xl font-bold text-gray-900">{getEditorName(editor)}</h1>

                <p className="mt-2 text-sm text-gray-500">
                  سطح همکاری: {getLevelLabel(editor.level)}
                </p>

                <div className="mt-5 grid gap-3 sm:grid-cols-4">
                  <div className="rounded-2xl bg-gray-50 p-4 text-center">
                    <div className="text-lg font-bold text-gray-900">
                      {Number(editor.rating_average || 0).toFixed(1)}
                    </div>
                    <div className="mt-1 text-xs text-gray-500">امتیاز</div>
                  </div>

                  <div className="rounded-2xl bg-gray-50 p-4 text-center">
                    <div className="text-lg font-bold text-gray-900">
                      {editor.completed_orders_count}
                    </div>
                    <div className="mt-1 text-xs text-gray-500">پروژه تکمیل‌شده</div>
                  </div>

                  <div className="rounded-2xl bg-gray-50 p-4 text-center">
                    <div className="text-lg font-bold text-gray-900">
                      {editor.base_price.toLocaleString('fa-IR')}
                    </div>
                    <div className="mt-1 text-xs text-gray-500">قیمت پایه</div>
                  </div>

                  <div className="rounded-2xl bg-gray-50 p-4 text-center">
                    <div className="text-lg font-bold text-gray-900">
                      {editor.average_delivery_hours} ساعت
                    </div>
                    <div className="mt-1 text-xs text-gray-500">میانگین تحویل</div>
                  </div>
                </div>

                <div className="mt-6">
                  <h2 className="mb-2 text-lg font-semibold text-gray-900">درباره ادیتور</h2>
                  <p className="text-sm leading-7 text-gray-600">
                    {editor.bio || 'هنوز توضیحی برای این ادیتور ثبت نشده است.'}
                  </p>
                </div>

                {editor.skills.length > 0 && (
                  <div className="mt-6">
                    <h2 className="mb-3 text-lg font-semibold text-gray-900">مهارت‌ها</h2>
                    <div className="flex flex-wrap gap-2">
                      {editor.skills.map((skill) => (
                        <span
                          key={skill.id}
                          className="rounded-full bg-violet-50 px-3 py-1 text-xs font-medium text-violet-700"
                        >
                          {getSkillLabel(skill)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-8 flex flex-wrap gap-3">
                  <Link
                    href={`/orders/new?editor=${editor.id}`}
                    className="rounded-2xl bg-gray-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-gray-800"
                  >
                    ثبت سفارش با این ادیتور
                  </Link>

                  <Link
                    href="/editors"
                    className="rounded-2xl border border-gray-200 bg-white px-5 py-3 text-sm font-medium text-gray-700 transition hover:bg-gray-50"
                  >
                    مشاهده سایر ادیتورها
                  </Link>
                </div>
              </div>
            </div>

            {editor.portfolio_items && editor.portfolio_items.length > 0 && (
              <div className="mt-10">
                <h2 className="mb-4 text-xl font-semibold text-gray-900">نمونه‌کارها</h2>
                <div className="grid gap-4 sm:grid-cols-2">
                  {editor.portfolio_items.map((item) => {
                    const image = item.after_image || item.before_image || null;

                    return (
                      <div
                        key={item.id}
                        className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm"
                      >
                        {image ? (
                          <img
                            src={image}
                            alt={item.title}
                            className="h-56 w-full object-cover"
                          />
                        ) : (
                          <div className="flex h-56 items-center justify-center bg-gray-100 text-sm text-gray-400">
                            تصویر نمونه‌کار موجود نیست
                          </div>
                        )}

                        <div className="p-4">
                          <h3 className="font-semibold text-gray-900">{item.title}</h3>

                          {item.style_title && (
                            <p className="mt-1 text-xs font-medium text-violet-700">
                              {item.style_title}
                            </p>
                          )}

                          {item.description && (
                            <p className="mt-2 text-sm leading-6 text-gray-600">
                              {item.description}
                            </p>
                          )}
                          <Link
                            href={`/portfolio/${item.id}`}
                            className="mt-4 inline-flex rounded-xl bg-violet-50 px-4 py-2 text-xs font-bold text-violet-700"
                          >
                            لایک، دیدگاه و مشاهده Before / After
                          </Link>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </section>
        )}
      </div>
    </main>
  );
}