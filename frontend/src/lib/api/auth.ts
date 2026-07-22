import { apiClient } from '@/lib/api/client';
import type { AuthUser, LoginPayload, RefreshResponse, RegisterPayload, SocialAuthExchangeResponse, TokenPair } from '@/lib/types/auth';
const PASSWORD_RESET_NOT_READY='بازیابی رمز عبور هنوز در Backend فعال نشده است.';
export const authAPI={
 async login(payload:LoginPayload):Promise<TokenPair>{return (await apiClient.post<TokenPair>('/auth/token/',payload)).data;},
 async refresh(refresh:string):Promise<RefreshResponse>{return (await apiClient.post<RefreshResponse>('/auth/token/refresh/',{refresh})).data;},
 async getMe():Promise<AuthUser>{return (await apiClient.get<AuthUser>('/accounts/me/')).data;},
 async register(payload:RegisterPayload):Promise<AuthUser>{return (await apiClient.post<AuthUser>('/accounts/register/',payload)).data;},
 async exchangeSocialCode(code:string):Promise<SocialAuthExchangeResponse>{return (await apiClient.post<SocialAuthExchangeResponse>('/accounts/social/exchange/',{code})).data;},
 async forgotPassword(_email:string):Promise<never>{throw new Error(PASSWORD_RESET_NOT_READY);},
 async verifyOTP(_email:string,_code:string):Promise<never>{throw new Error(PASSWORD_RESET_NOT_READY);},
 async resetPassword(_code:string,_newPassword:string):Promise<never>{throw new Error(PASSWORD_RESET_NOT_READY);},
};
