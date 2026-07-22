import { apiClient } from '@/lib/api/client';
import type {
  AuthUser,
  LoginPayload,
  RefreshResponse,
  RegisterPayload,
  TokenPair,
} from '@/lib/types/auth';

const PASSWORD_RESET_NOT_READY =
  'بازیابی رمز عبور هنوز در Backend فعال نشده است. این قابلیت در فاز بعدی احراز هویت تکمیل می‌شود.';

export const authAPI = {
  async login(payload: LoginPayload): Promise<TokenPair> {
    const response = await apiClient.post<TokenPair>(
      '/auth/token/',
      payload,
    );
    return response.data;
  },

  async refresh(refresh: string): Promise<RefreshResponse> {
    const response = await apiClient.post<RefreshResponse>(
      '/auth/token/refresh/',
      { refresh },
    );
    return response.data;
  },

  async getMe(): Promise<AuthUser> {
    const response = await apiClient.get<AuthUser>('/accounts/me/');
    return response.data;
  },

  async register(payload: RegisterPayload): Promise<AuthUser> {
    const response = await apiClient.post<AuthUser>(
      '/accounts/register/',
      payload,
    );

    return response.data;
  },

  async forgotPassword(_email: string): Promise<never> {
    throw new Error(PASSWORD_RESET_NOT_READY);
  },

  async verifyOTP(_email: string, _code: string): Promise<never> {
    throw new Error(PASSWORD_RESET_NOT_READY);
  },

  async resetPassword(_code: string, _newPassword: string): Promise<never> {
    throw new Error(PASSWORD_RESET_NOT_READY);
  },
};
