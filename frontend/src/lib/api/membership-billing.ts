import { apiClient } from '@/lib/api/client';

export const membershipBillingAPI = {
  async purchase(tierId: number, period: 'monthly' | 'annual') {
    const response = await apiClient.post(
      '/customer/membership/purchase/',
      { tier_id: tierId, period },
    );
    return response.data;
  },
};
