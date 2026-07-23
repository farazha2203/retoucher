'use client';

import { Heart, Medal, Star, TrendingUp } from 'lucide-react';

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-[34px] bg-gradient-to-l from-[#e9e1f8] to-[#e1f3eb] p-8">
        <TrendingUp className="text-[#735c9b]"/>
        <h1 className="mt-4 text-3xl font-black text-[#40354b]">رتبه و عملکرد من</h1>
        <p className="mt-3 text-sm text-[#7e7386]">
          امتیاز، لایک، سفارش‌های تکمیل‌شده و سطح کمیسیون.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {[
          [Star,'امتیاز'],
          [Heart,'لایک نمونه‌کار'],
          [Medal,'رتبه'],
        ].map(([Icon,title]: any) => (
          <article key={title} className="rounded-[28px] bg-white/70 p-6 shadow-sm">
            <Icon className="text-[#9a78bc]"/>
            <strong className="mt-4 block text-3xl">—</strong>
            <span className="text-xs text-[#897e90]">{title}</span>
          </article>
        ))}
      </section>
    </div>
  );
}
