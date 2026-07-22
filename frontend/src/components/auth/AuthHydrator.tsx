'use client';

import { useEffect, useRef } from 'react';

import { authAPI } from '@/lib/api/auth';
import { useAuthStore } from '@/lib/stores/auth.store';

export function AuthHydrator() {
  const started = useRef(false);
  const hydrated = useAuthStore((state) => state.hydrated);
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  useEffect(() => {
    if (!hydrated || started.current || !accessToken || user) {
      return;
    }

    started.current = true;

    authAPI
      .getMe()
      .then(setUser)
      .catch(() => clearAuth());
  }, [accessToken, clearAuth, hydrated, setUser, user]);

  return null;
}
