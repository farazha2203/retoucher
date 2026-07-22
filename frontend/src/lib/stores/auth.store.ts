'use client';

import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

import type { AuthUser } from '@/lib/types/auth';

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  hydrated: boolean;
  setAuth: (
    user: AuthUser,
    accessToken: string,
    refreshToken: string,
  ) => void;
  setUser: (user: AuthUser | null) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  clearAuth: () => void;
  markHydrated: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      hydrated: false,

      setAuth: (user, accessToken, refreshToken) =>
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
        }),

      setUser: (user) =>
        set((state) => ({
          user,
          isAuthenticated: Boolean(user && state.accessToken),
        })),

      setTokens: (accessToken, refreshToken) =>
        set({
          accessToken,
          refreshToken,
          isAuthenticated: true,
        }),

      clearAuth: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        }),

      markHydrated: () =>
        set((state) => ({
          hydrated: true,
          isAuthenticated: Boolean(state.accessToken),
        })),
    }),
    {
      name: 'retoucher-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
      onRehydrateStorage: () => (state) => {
        state?.markHydrated();
      },
    },
  ),
);
