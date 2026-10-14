import { useQuery } from '@tanstack/react-query';
import { fetchBackendHealth } from '../services/healthService';

/**
 * Custom hook to monitor backend health using TanStack Query.
 */
export const useHealth = () => {
  return useQuery({
    queryKey: ['backendHealth'],
    queryFn: fetchBackendHealth,
    refetchInterval: 30000,
    retry: 2,
  });
};
