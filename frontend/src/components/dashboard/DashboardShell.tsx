'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Bell,
  BriefcaseBusiness,
  FolderKanban,
  Home,
  LogOut,
  Menu,
  Settings,
  UserRound,
  WalletCards,
  X,
} from 'lucide-react';
import { useState } from 'react';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuthStore } from '@/lib/stores/auth.store';

const baseItems = [
  { href: '/dashboard', label: 'نمای کلی', icon: Home },
  { href: '/dashboard/orders', label: 'سفارش‌ها', icon: BriefcaseBusiness },
  { href: '/dashboard/projects', label: 'درخواست‌ها', icon: FolderKanban },
  { href: '/dashboard/wallet', label: 'کیف پول', icon: WalletCards },
  { href: '/dashboard/notifications', label: 'اعلان‌ها', icon: Bell },
  { href: '/dashboard/settings', label: 'تنظیمات', icon: Settings },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const user = useAuthStore((state) => state.user);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  const logout = () => {
    clearAuth();
    window.location.assign('/login');
  };

  const sidebar = (
    <aside className="flex h-full flex-col bg-[#2F261E] text-white">
      <div className="flex h-20 items-center justify-between border-b border-white/10 px-5">
        <Link href="/" className="text-lg font-black">ریتاچر</Link>
        <button
          type="button"
          className="lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-label="بستن منو"
        >
          <X size={22} />
        </button>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {baseItems.map(({ href, label, icon: Icon }) => {
          const active =
            href === '/dashboard'
              ? pathname === href
              : pathname.startsWith(href);

          return (
            <Link
              key={href}
              href={href}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm transition ${
                active
                  ? 'bg-white text-[#2F261E]'
                  : 'text-white/75 hover:bg-white/10 hover:text-white'
              }`}
            >
              <Icon size={18} />
              <span className="font-bold">{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-4">
        <div className="mb-3 flex items-center gap-3 rounded-xl bg-white/5 p-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/10">
            <UserRound size={18} />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-bold">
              {user?.first_name || user?.username}
            </p>
            <p className="text-xs text-white/50">{user?.role}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={logout}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-white/15 px-4 py-2.5 text-sm font-bold hover:bg-white/10"
        >
          <LogOut size={16} />
          خروج
        </button>
      </div>
    </aside>
  );

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[#F7F4EF]">
        <div className="fixed inset-y-0 right-0 z-40 hidden w-72 lg:block">
          {sidebar}
        </div>

        {mobileOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <button
              type="button"
              className="absolute inset-0 bg-black/40"
              onClick={() => setMobileOpen(false)}
              aria-label="بستن منو"
            />
            <div className="absolute inset-y-0 right-0 w-72">{sidebar}</div>
          </div>
        )}

        <div className="lg:pr-72">
          <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[#E5DDD2] bg-white/95 px-4 backdrop-blur sm:px-8">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              className="rounded-xl border border-[#E5DDD2] p-2 lg:hidden"
              aria-label="باز کردن منو"
            >
              <Menu size={20} />
            </button>
            <div>
              <p className="text-xs text-[#8A7E72]">پنل کاربری</p>
              <p className="text-sm font-black text-[#352B23]">
                {user?.first_name || user?.username}
              </p>
            </div>
            <Link
              href="/"
              className="rounded-xl border border-[#E5DDD2] px-3 py-2 text-xs font-bold text-[#51473E]"
            >
              صفحه اصلی
            </Link>
          </header>

          <div className="p-4 sm:p-8">{children}</div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
