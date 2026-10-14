import { describe, it, expect, vi, beforeEach } from 'vitest';
import apiClient from '../api/client';
import { registerUser, loginUser, fetchCurrentUser, logoutUser } from '../services/authService';

vi.mock('../api/client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('authService', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('registerUser stores access token in localStorage on success', async () => {
    const mockData = {
      access_token: 'fake-jwt-token-123',
      token_type: 'bearer',
      user: { id: 1, email: 'test@example.com' },
    };
    apiClient.post.mockResolvedValueOnce({ data: mockData });

    const result = await registerUser({ email: 'test@example.com', password: 'Password123!' });
    expect(result).toEqual(mockData);
    expect(localStorage.getItem('access_token')).toBe('fake-jwt-token-123');
  });

  it('loginUser stores access token in localStorage on success', async () => {
    const mockData = {
      access_token: 'login-token-456',
      token_type: 'bearer',
      user: { id: 2, email: 'user@example.com' },
    };
    apiClient.post.mockResolvedValueOnce({ data: mockData });

    const result = await loginUser({ email: 'user@example.com', password: 'Password123!' });
    expect(result).toEqual(mockData);
    expect(localStorage.getItem('access_token')).toBe('login-token-456');
  });

  it('fetchCurrentUser calls /auth/me and returns user data', async () => {
    const mockUser = { id: 1, email: 'me@example.com', full_name: 'Me User' };
    apiClient.get.mockResolvedValueOnce({ data: mockUser });

    const result = await fetchCurrentUser();
    expect(apiClient.get).toHaveBeenCalledWith('/auth/me');
    expect(result).toEqual(mockUser);
  });

  it('logoutUser removes access_token from localStorage', () => {
    localStorage.setItem('access_token', 'temp-token');
    logoutUser();
    expect(localStorage.getItem('access_token')).toBeNull();
  });
});
