'use client';

import Link from 'next/link';
import {
  ArrowLeft,
  BriefcaseBusiness,
  FolderKanban,
  Heart,
  Sparkles,
  Star,
  WalletCards,
} from 'lucide-react';

import { useAuthStore } from '@/lib/stores/auth.store';

const cards = [
  {
    label: 'سفارش‌های فعال',
    value: '—',
    icon: BriefcaseBusiness,
    bg: 'from-[#fae1eb] to-[#f8edf3]',
    iconBg: 'bg-[#f5c8d9] text-[#b85e7e]',
  },
  {
    label: 'پروژه‌های من',
    value: '—',
    icon: FolderKanban,
    bg: 'from-[#ebe4fa] to-[#f5f1fc]',
    iconBg: 'bg-[#d9cdf3] text-[#765ca5]',
  },
  {
    label: 'کیف پول',
    value: '—',
    icon: WalletCards,
    bg: 'from-[#dff2e9] to-[#eff9f4]',
    iconBg: 'bg-[#bfe2d2] text-[#477f69]',
  },
  {
    label: 'امتیاز و محبوبیت',
    value: '—',
    icon: Star,
    bg: 'from-[#fff0d9] to-[#fff8eb]',
    iconBg: 'bg-[#f6ddb4] text-[#9d7436]',
  },
];

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[36px] border border-white/80 bg-white/62 p-7 shadow-[0_30px_80px_rgba(106,84,130,.10)] backdrop-blur-2xl sm:p-9">
        <div className="absolute -left-16 -top-20 h-64 w-64 rounded-full bg-[#e7d8fa]/65 blur-3xl"/>
        <div className="absolute -bottom-24 right-10 h-64 w-64 rounded-full bg-[#d6f0e4]/70 blur-3xl"/>

        <div className="relative grid gap-8 lg:grid-cols-[1fr_320px] lg:items-center">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-[#f2ebfa] px-4 py-2 text-xs font-black text-[#7a61a0]">
              <Sparkles size={15}/>
              داشبورد نسل جدید
            </span>
            <h1 className="mt-5 text-3xl font-black leading-relaxed text-[#3e3447] sm:text-4xl">
              سلام {user?.first_name || user?.username}،
              <span className="text-[#c46f91]"> امروز چی می‌سازیم؟</span>
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-8 text-[#817689]">
              سفارش، پروژه، فایل، پرداخت، رتبه و اشتراک را از یک فضای آرام و حرفه‌ای مدیریت کن.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                href="/dashboard/orders/new"
                className="rounded-[18px] bg-[#6f57a0] px-5 py-3 text-sm font-black text-white shadow-lg shadow-purple-200"
              >
                ثبت سفارش
              </Link>
              <Link
                href="/dashboard/editors"
                className="rounded-[18px] bg-white px-5 py-3 text-sm font-black text-[#705b87] shadow-sm"
              >
                انتخاب ادیتور
              </Link>
            </div>
          </div>

          <div className="rounded-[30px] border border-white/80 bg-gradient-to-br from-[#fae8f0]/80 via-[#eee7fb]/80 to-[#e1f3eb]/80 p-6">
            <Heart className="text-[#c36d8e]" fill="currentColor"/>
            <strong className="mt-4 block text-2xl text-[#45394f]">
              تجربه شخصی‌سازی‌شده
            </strong>
            <p className="mt-2 text-xs leading-6 text-[#82758b]">
              کارت‌ها و میانبرها بر اساس نقش مشتری، آتلیه یا ادیتور تغییر می‌کنند.
            </p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map(({label,value,icon:Icon,bg,iconBg}) => (
          <article
            key={label}
            className={`rounded-[28px] border border-white/80 bg-gradient-to-br ${bg} p-5 shadow-sm`}
          >
            <div className="flex items-center justify-between">
              <span className={`grid h-12 w-12 place-items-center rounded-[18px] ${iconBg}`}>
                <Icon size={20}/>
              </span>
              <strong className="text-3xl text-[#43384b]">{value}</strong>
            </div>
            <p className="mt-5 text-sm font-bold text-[#746879]">{label}</p>
          </article>
        ))}
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        {[
          ['/dashboard/profile','پروفایل کامل','هویت، آدرس و اطلاعات آتلیه'],
          ['/dashboard/membership','اشتراک و تخفیف','پلن آتلیه و VIP'],
          ['/dashboard/orders','سفارش‌های من','Workflow، فایل و تحویل'],
        ].map(([href,title,text]) => (
          <Link
            key={href}
            href={href}
            className="group flex items-center gap-4 rounded-[26px] border border-white/80 bg-white/68 p-5 shadow-sm backdrop-blur-xl transition hover:-translate-y-1 hover:shadow-xl"
          >
            <div className="flex-1">
              <strong className="text-[#463b4f]">{title}</strong>
              <p className="mt-1 text-xs text-[#918697]">{text}</p>
            </div>
            <ArrowLeft className="text-[#a694b9] transition group-hover:-translate-x-1" size={18}/>
          </Link>
        ))}
      </section>
    </div>
  );
}
