import { useState, useEffect, createContext, useContext } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchCurrentUser, loginUser, registerUser, logoutUser } from '../services/authService';
import { fetchActiveResume } from '../services/skillGapService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const queryClient = useQueryClient();
  const [token, setToken] = useState(() => localStorage.getItem('access_token'));

  // Sync token state if changed
  useEffect(() => {
    const handleStorageChange = () => {
      setToken(localStorage.getItem('access_token'));
    };
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const {
    data: user,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['currentUser', token],
    queryFn: fetchCurrentUser,
    enabled: !!token,
    retry: false,
    staleTime: 1000 * 60 * 10,
  });

  // Automatically fetch active resume on login and on app load if a valid session exists
  const {
    data: activeResumeData,
    isLoading: isLoadingActiveResume,
    refetch: refetchActiveResume,
  } = useQuery({
    queryKey: ['activeResume', token],
    queryFn: fetchActiveResume,
    enabled: !!token && !!user,
    retry: false,
    staleTime: 1000 * 30,
  });

  const loginMutation = useMutation({
    mutationFn: loginUser,
    onSuccess: (data) => {
      setToken(data.access_token);
      queryClient.setQueryData(['currentUser', data.access_token], data.user);
      queryClient.invalidateQueries({ queryKey: ['activeResume'] });
    },
  });

  const registerMutation = useMutation({
    mutationFn: registerUser,
    onSuccess: (data) => {
      setToken(data.access_token);
      queryClient.setQueryData(['currentUser', data.access_token], data.user);
      queryClient.invalidateQueries({ queryKey: ['activeResume'] });
    },
  });

  const logout = () => {
    logoutUser();
    setToken(null);
    queryClient.removeQueries({ queryKey: ['currentUser'] });
    queryClient.removeQueries({ queryKey: ['activeResume'] });
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isAuthenticated: !!token && !!user,
        isLoading,
        isError,
        activeResumeData,
        isLoadingActiveResume,
        refetchActiveResume,
        login: loginMutation.mutateAsync,
        register: registerMutation.mutateAsync,
        isLoggingIn: loginMutation.isPending,
        isRegistering: registerMutation.isPending,
        loginError: loginMutation.error,
        registerError: registerMutation.error,
        logout,
        refetchUser: refetch,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
