 'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  Clock3,
  ImageIcon,
  Search,
  Sparkles,
  Star,
} from 'lucide-react';
import { useMemo, useState } from 'react';

import { editorsAPI } from '@/lib/api/editors';

export default function EditorsPage() {
  const [query, setQuery] = useState('');
  const editors = useQuery({
    queryKey: ['editors'],
    queryFn: editorsAPI.list,
  });

  const rows = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return editors.data || [];

    return (editors.data || []).filter((editor) => {
      const source = [
        editor.display_name,
        editor.username,
        editor.bio,
        ...editor.skills.map((skill) => skill.title),
      ]
        .join(' ')
        .toLowerCase();

      return source.includes(normalized);
    });
  }, [editors.data, query]);

  return (
    <div>
      <section className="relative overflow-hidden rounded-[32px] bg-gradient-to-l from-[#392b50] to-[#735797] p-7 text-white">
        <Sparkles className="absolute left-8 top-7 text-white/15" size={80} />
        <div className="relative">
          <span className="text-xs font-bold text-[#ffc1d8]">
            بازار خلاقان ریتاچر
          </span>
          <h1 className="mt-2 text-3xl font-black">
            ادیتور مناسب پروژه‌ات را پیدا کن
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-8 text-white/65">
            نمونه‌کار Before / After، مهارت‌ها، امتیاز، قیمت پایه و
            زمان تحویل ادیتورها را مقایسه کن.
          </p>
        </div>
      </section>

      <div className="relative mt-6">
        <Search
          size={19}
          className="absolute right-4 top-1/2 -translate-y-1/2 text-[#9a91a2]"
        />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="جستجوی نام، مهارت یا سبک ادیت..."
          className="w-full rounded-2xl border border-[#e9e3ee] bg-white py-4 pl-4 pr-12 text-sm outline-none focus:border-[#a78de5] focus:ring-4 focus:ring-purple-100"
        />
      </div>

      {editors.isLoading && (
        <div className="mt-6 rounded-3xl bg-white p-8 text-center text-sm text-[#867d8e]">
          در حال دریافت ادیتورها...
        </div>
      )}

      {editors.isError && (
        <div className="mt-6 rounded-3xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          دریافت لیست ادیتورها ناموفق بود.
        </div>
      )}

      <section className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {rows.map((editor) => (
          <article
            key={editor.id}
            className="overflow-hidden rounded-[28px] border border-[#ebe5ef] bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-xl hover:shadow-purple-100/60"
          >
            <div className="h-2 bg-gradient-to-l from-[#e17aa1] via-[#a58be6] to-[#75bea0]" />
            <div className="p-5">
              <div className="flex items-start gap-3">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#f6d5e2] to-[#ddd3f6] text-xl font-black text-[#7d6092]">
                  {(editor.display_name || editor.username)
                    .slice(0, 1)
                    .toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <h2 className="truncate text-base font-black text-[#403647]">
                    {editor.display_name || editor.username}
                  </h2>
                  <div className="mt-1 flex items-center gap-2 text-xs text-[#8e8496]">
                    <Star size={14} className="fill-amber-400 text-amber-400" />
                    <span>{editor.rating_average}</span>
                    <span>·</span>
                    <span>{editor.completed_orders_count} سفارش</span>
                  </div>
                </div>
                {editor.is_available && (
                  <span className="rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-bold text-emerald-600">
                    آماده همکاری
                  </span>
                )}
              </div>

              <p className="mt-4 line-clamp-3 min-h-[72px] text-xs leading-6 text-[#867c8e]">
                {editor.bio || 'توضیحی برای این ادیتور ثبت نشده است.'}
              </p>

              <div className="mt-4 flex flex-wrap gap-1.5">
                {editor.skills.slice(0, 4).map((skill) => (
                  <span
                    key={skill.id}
                    className="rounded-full bg-[#f4f0f9] px-2.5 py-1 text-[10px] font-bold text-[#78658e]"
                  >
                    {skill.title}
                  </span>
                ))}
              </div>

              <div className="mt-5 grid grid-cols-3 border-y border-[#f0ebf3] py-4 text-center">
                <div>
                  <ImageIcon className="mx-auto text-[#d66f98]" size={17} />
                  <strong className="mt-2 block text-xs text-[#4f4556]">
                    {editor.portfolio_items?.length || 0}
                  </strong>
                  <span className="text-[9px] text-[#9b929f]">نمونه‌کار</span>
                </div>
                <div>
                  <Clock3 className="mx-auto text-[#846bd1]" size={17} />
                  <strong className="mt-2 block text-xs text-[#4f4556]">
                    {editor.average_delivery_hours} ساعت
                  </strong>
                  <span className="text-[9px] text-[#9b929f]">تحویل متوسط</span>
                </div>
                <div>
                  <Star className="mx-auto text-[#56a887]" size={17} />
                  <strong className="mt-2 block text-xs text-[#4f4556]">
                    {Number(editor.base_price).toLocaleString('fa-IR')}
                  </strong>
                  <span className="text-[9px] text-[#9b929f]">قیمت پایه</span>
                </div>
              </div>

              <div className="mt-5 flex gap-2">
                <Link
                  href={`/dashboard/editors/${editor.id}`}
                  className="flex-1 rounded-2xl bg-[#f0ebf7] px-4 py-3 text-center text-xs font-black text-[#765e94]"
                >
                  مشاهده پروفایل
                </Link>
                {editor.accepts_direct_requests && (
                  <Link
                    href={`/dashboard/projects/new?editor=${editor.id}`}
                    className="flex-1 rounded-2xl bg-gradient-to-l from-[#df79a0] to-[#9278db] px-4 py-3 text-center text-xs font-black text-white"
                  >
                    درخواست مستقیم
                  </Link>
                )}
              </div>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
