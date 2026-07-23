'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Bell,
  BriefcaseBusiness,
  Building2,
  Crown,
  FolderKanban,
  Home,
  Images,
  LogOut,
  Menu,
  Settings,
  Sparkles,
  UserRound,
  UsersRound,
  WalletCards,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { useMemo, useState } from 'react';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuthStore } from '@/lib/stores/auth.store';

type NavItem = readonly [string, string, LucideIcon];

const common: NavItem[] = [
  ['/dashboard', 'نمای کلی', Home],
  ['/dashboard/orders', 'سفارش‌ها', BriefcaseBusiness],
  ['/dashboard/projects', 'پروژه‌ها', FolderKanban],
  ['/dashboard/editors', 'ادیتورها', UsersRound],
  ['/dashboard/wallet', 'کیف پول', WalletCards],
  ['/dashboard/profile', 'پروفایل', UserRound],
  ['/dashboard/membership', 'اشتراک و تخفیف', Crown],
  ['/dashboard/notifications', 'اعلان‌ها', Bell],
  ['/dashboard/settings', 'تنظیمات', Settings],
];

const editorOnly: NavItem[] = [
  ['/dashboard/editor-workspace', 'فضای کاری ادیتور', Images],
  ['/dashboard/analytics', 'آمار و رتبه من', Sparkles],
];

const studioOnly: NavItem[] = [
  ['/dashboard/studio', 'آتلیه و تبلیغات', Building2],
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.user);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const [open, setOpen] = useState(false);

  const items = useMemo(() => {
    const rows = [...common];
    if (user?.role === 'editor') rows.splice(5, 0, ...editorOnly);
    if (user?.role === 'client') rows.splice(7, 0, ...studioOnly);
    return rows;
  }, [user?.role]);

  const sidebar = (
    <aside className="flex h-full flex-col rounded-[30px] border border-white/80 bg-white/70 p-4 shadow-[0_24px_80px_rgba(116,93,142,.12)] backdrop-blur-2xl">
      <Link href="/" className="flex items-center gap-3 rounded-[24px] p-3">
        <span className="grid h-12 w-12 place-items-center rounded-[18px] bg-gradient-to-br from-[#f1a9c1] via-[#c7a8ed] to-[#8fcbb1] text-xl text-white shadow-lg shadow-purple-200/50">✦</span>
        <div>
          <strong className="block text-lg text-[#3f3549]">ریتاچر</strong>
          <span className="text-[10px] text-[#9a8fa3]">Creative workspace</span>
        </div>
      </Link>

      <div className="my-4 rounded-[26px] bg-gradient-to-br from-[#faeaf1] via-[#f0ebfb] to-[#e7f5ee] p-4">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-white/70 text-[#856ea3]">
            <UserRound size={20}/>
          </span>
          <div className="min-w-0">
            <strong className="block truncate text-sm text-[#4b4054]">{user?.first_name || user?.username}</strong>
            <span className="text-[10px] text-[#8c7f96]">{user?.role === 'editor' ? 'ادیتور حرفه‌ای' : 'مشتری ریتاچر'}</span>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto">
        {items.map(([href,label,Icon]) => {
          const active = href === '/dashboard' ? pathname === href : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={`flex items-center gap-3 rounded-[18px] px-4 py-3 text-sm transition ${
                active
                  ? 'bg-[#ede6f8] font-black text-[#6f56a0] shadow-sm'
                  : 'text-[#786d80] hover:bg-white hover:text-[#5f4c73]'
              }`}
            >
              <span className={`grid h-9 w-9 place-items-center rounded-[14px] ${
                active ? 'bg-white text-[#8b70bd]' : 'bg-[#f8f5fa] text-[#9a8fa3]'
              }`}>
                <Icon size={17}/>
              </span>
              {label}
            </Link>
          );
        })}
      </nav>

      <button
        onClick={() => {
          clearAuth();
          window.location.assign('/login');
        }}
        className="mt-3 flex items-center justify-center gap-2 rounded-[18px] bg-[#fff1f4] p-3 text-sm font-bold text-[#c56b86]"
      >
        <LogOut size={17}/>
        خروج
      </button>
    </aside>
  );

  return (
    <ProtectedRoute>
      <div
        dir="rtl"
        className="min-h-screen bg-[radial-gradient(circle_at_90%_0%,#f9e7ef_0,transparent_24%),radial-gradient(circle_at_0%_80%,#e5f4ed_0,transparent_28%),#f7f5fa]"
      >
        <div className="fixed inset-y-0 right-0 z-40 hidden w-[292px] p-3 lg:block">
          {sidebar}
        </div>

        {open && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <button
              className="absolute inset-0 bg-[#3b3046]/30 backdrop-blur-sm"
              onClick={() => setOpen(false)}
              aria-label="بستن منو"
            />
            <div className="absolute inset-y-0 right-0 w-[292px] p-3">
              {sidebar}
            </div>
          </div>
        )}

        <div className="lg:pr-[292px]">
          <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-white/80 bg-white/55 px-4 backdrop-blur-2xl sm:px-8">
            <button
              onClick={() => setOpen(true)}
              className="rounded-2xl bg-white p-3 shadow-sm lg:hidden"
              aria-label="باز کردن منو"
            >
              <Menu size={20}/>
            </button>
            <div>
              <p className="text-[11px] text-[#a095a8]">فضای کاری شخصی</p>
              <strong className="text-sm text-[#4a4052]">داشبورد هوشمند ریتاچر</strong>
            </div>
            <Link
              href="/dashboard/notifications"
              className="rounded-2xl bg-white p-3 text-[#79668f] shadow-sm"
            >
              <Bell size={19}/>
            </Link>
          </header>

          <main className="p-4 sm:p-7">{children}</main>
        </div>
      </div>
    </ProtectedRoute>
  );
}
