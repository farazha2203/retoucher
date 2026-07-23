import { apiClient } from '@/lib/api/client';
import type { CustomerProfile, CustomerTier } from '@/lib/types/customer';
export const customerAPI={
 getProfile:async()=> (await apiClient.get<CustomerProfile>('/customer/profile/me/')).data,
 updateProfile:async(payload:Partial<CustomerProfile>)=> (await apiClient.patch<CustomerProfile>('/customer/profile/me/',payload)).data,
 getTiers:async()=> (await apiClient.get<CustomerTier[]>('/customer/tiers/')).data,
};
