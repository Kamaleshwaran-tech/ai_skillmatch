import apiClient from '../api/client';

/**
 * Register a new user account.
 * @param {Object} data { email, password, full_name }
 * @returns {Promise<Object>} { access_token, token_type, user }
 */
export const registerUser = async (data) => {
  const response = await apiClient.post('/auth/register', data);
  if (response.data.access_token) {
    localStorage.setItem('access_token', response.data.access_token);
  }
  return response.data;
};

/**
 * Login with user credentials.
 * @param {Object} data { email, password }
 * @returns {Promise<Object>} { access_token, token_type, user }
 */
export const loginUser = async (data) => {
  const response = await apiClient.post('/auth/login', data);
  if (response.data.access_token) {
    localStorage.setItem('access_token', response.data.access_token);
  }
  return response.data;
};

/**
 * Get current authenticated user details.
 * @returns {Promise<Object>} User object
 */
export const fetchCurrentUser = async () => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};

/**
 * Logout and clear token.
 */
export const logoutUser = () => {
  localStorage.removeItem('access_token');
};
