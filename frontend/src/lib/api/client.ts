import axios, {
  AxiosError,
  AxiosHeaders,
  InternalAxiosRequestConfig,
} from 'axios';

import { useAuthStore } from '@/lib/stores/auth.store';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
});

type RetriableRequest = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

let refreshPromise: Promise<string> | null = null;

function applyAuthorization(
  config: InternalAxiosRequestConfig,
  accessToken: string,
) {
  const headers = AxiosHeaders.from(config.headers);
  headers.set('Authorization', `Bearer ${accessToken}`);
  config.headers = headers;
  return config;
}

apiClient.interceptors.request.use((config) => {
  const accessToken = useAuthStore.getState().accessToken;

  if (accessToken) {
    return applyAuthorization(config, accessToken);
  }

  return config;
});

async function refreshAccessToken(): Promise<string> {
  const { refreshToken, setTokens, clearAuth } = useAuthStore.getState();

  if (!refreshToken) {
    clearAuth();
    throw new Error('Refresh token is unavailable.');
  }

  try {
    const response = await axios.post<{
      access: string;
      refresh?: string;
    }>(`${API_BASE_URL}/auth/token/refresh/`, {
      refresh: refreshToken,
    });

    const nextRefresh = response.data.refresh || refreshToken;
    setTokens(response.data.access, nextRefresh);
    return response.data.access;
  } catch (error) {
    clearAuth();
    throw error;
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const request = error.config as RetriableRequest | undefined;

    if (error.response?.status !== 401 || !request || request._retry) {
      return Promise.reject(error);
    }

    request._retry = true;

    if (!refreshPromise) {
      refreshPromise = refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
    }

    try {
      const accessToken = await refreshPromise;
      return apiClient(applyAuthorization(request, accessToken));
    } catch (refreshError) {
      if (typeof window !== 'undefined') {
        const next = encodeURIComponent(
          `${window.location.pathname}${window.location.search}`,
        );
        window.location.assign(`/login?next=${next}`);
      }

      return Promise.reject(refreshError);
    }
  },
);

export function getApiErrorMessage(
  error: unknown,
  fallback = 'خطایی رخ داده است. دوباره تلاش کنید.',
): string {
  if (!axios.isAxiosError(error)) {
    return fallback;
  }

  const data = error.response?.data as
    | { detail?: string; message?: string; non_field_errors?: string[] }
    | undefined;

  return (
    data?.detail ||
    data?.message ||
    data?.non_field_errors?.[0] ||
    fallback
  );
}
