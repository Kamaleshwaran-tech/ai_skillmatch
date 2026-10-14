import apiClient from '../api/client';

/**
 * Service to fetch backend operational health.
 */
export const fetchBackendHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};
