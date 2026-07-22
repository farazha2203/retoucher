'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';

import { useAuthStore } from '@/lib/stores/auth.store';
import type { UserRole } from '@/lib/types/auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

export function ProtectedRoute({
  children,
  allowedRoles,
}: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const hydrated = useAuthStore((state) => state.hydrated);
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    if (!accessToken) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }

    if (user && allowedRoles && !allowedRoles.includes(user.role)) {
      router.replace('/dashboard');
    }
  }, [accessToken, allowedRoles, hydrated, pathname, router, user]);

  if (!hydrated || (accessToken && !user)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F8F6F2]">
        <div className="rounded-2xl border border-[#E7DED1] bg-white px-8 py-6 text-center shadow-sm">
          <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-2 border-[#D9CBBB] border-t-[#3D3022]" />
          <p className="text-sm text-[#675E54]">در حال آماده‌سازی حساب...</p>
        </div>
      </div>
    );
  }

  if (!accessToken || !user) {
    return null;
  }

  return children;
}
