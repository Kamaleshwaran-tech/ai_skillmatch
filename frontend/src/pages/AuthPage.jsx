import React, { useState } from 'react';
import {
  Container,
  Paper,
  Tabs,
  Tab,
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Stack,
  Card,
  CardContent,
  Chip,
  Divider,
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import PersonAddOutlinedIcon from '@mui/icons-material/PersonAddOutlined';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import LogoutIcon from '@mui/icons-material/Logout';
import { useAuth } from '../hooks/useAuth';

// Zod schemas for validation
const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

const registerSchema = z.object({
  fullName: z.string().min(2, 'Full name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

export const AuthPage = () => {
  const [tabIndex, setTabIndex] = useState(0);
  const [apiError, setApiError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const {
    user,
    isAuthenticated,
    login,
    register,
    logout,
    isLoggingIn,
    isRegistering,
  } = useAuth();

  // Login form
  const {
    register: loginRegister,
    handleSubmit: handleLoginSubmit,
    formState: { errors: loginErrors },
    reset: resetLoginForm,
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  // Register form
  const {
    register: regRegister,
    handleSubmit: handleRegSubmit,
    formState: { errors: regErrors },
    reset: resetRegForm,
  } = useForm({
    resolver: zodResolver(registerSchema),
    defaultValues: { fullName: '', email: '', password: '' },
  });

  const handleTabChange = (event, newIndex) => {
    setTabIndex(newIndex);
    setApiError('');
    setSuccessMsg('');
  };

  const onLogin = async (data) => {
    setApiError('');
    setSuccessMsg('');
    try {
      await login(data);
      setSuccessMsg('Successfully logged in!');
      resetLoginForm();
    } catch (err) {
      setApiError(
        err.response?.data?.detail || 'Failed to log in. Please check your credentials.'
      );
    }
  };

  const onRegister = async (data) => {
    setApiError('');
    setSuccessMsg('');
    try {
      await register({
        email: data.email,
        password: data.password,
        full_name: data.fullName,
      });
      setSuccessMsg('Account registered and authenticated successfully!');
      resetRegForm();
    } catch (err) {
      setApiError(
        err.response?.data?.detail || 'Registration failed. Email might already exist.'
      );
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 6 }}>
      {/* If authenticated, show Current User Profile Card */}
      {isAuthenticated && user ? (
        <Card variant="outlined" sx={{ p: 3, borderRadius: 2, boxShadow: 2, bgcolor: '#ffffff' }}>
          <CardContent>
            <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 2 }}>
              <CheckCircleIcon color="success" sx={{ fontSize: 32 }} />
              <Typography variant="h5" sx={{ fontWeight: 700 }}>
                Authenticated as {user.full_name || user.email}
              </Typography>
            </Stack>

            <Alert severity="success" sx={{ mb: 3 }}>
              Protected endpoint <code>GET /api/auth/me</code> verified successfully!
            </Alert>

            <Box sx={{ bgcolor: '#f8fafc', p: 2.5, borderRadius: 2, border: '1px solid #e2e8f0', mb: 3 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Current User Token Payload (GET /api/auth/me):
              </Typography>
              <Stack spacing={1} sx={{ mt: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">User ID:</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{user.id}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Email:</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{user.email}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Full Name:</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{user.full_name || 'N/A'}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Status:</Typography>
                  <Chip
                    label={user.is_active ? 'Active' : 'Inactive'}
                    size="small"
                    color={user.is_active ? 'success' : 'default'}
                  />
                </Box>
              </Stack>
            </Box>

            <Button
              id="signout-button"
              variant="outlined"
              color="error"
              fullWidth
              startIcon={<LogoutIcon />}
              onClick={() => {
                logout();
                setTabIndex(0);
              }}
              sx={{ py: 1.2 }}
            >
              Sign Out
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Paper elevation={3} sx={{ borderRadius: 2, overflow: 'hidden' }}>
          <Box sx={{ bgcolor: 'primary.main', color: 'primary.contrastText', p: 3, textAlign: 'center' }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              SkillSync AI Portal
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9, mt: 0.5 }}>
              Sign in or create an account to access skill analytics
            </Typography>
          </Box>

          <Tabs
            value={tabIndex}
            onChange={handleTabChange}
            variant="fullWidth"
            textColor="primary"
            indicatorColor="primary"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab icon={<LockOutlinedIcon />} iconPosition="start" label="Sign In" />
            <Tab icon={<PersonAddOutlinedIcon />} iconPosition="start" label="Register" />
          </Tabs>

          <Box sx={{ p: 4 }}>
            {apiError && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {apiError}
              </Alert>
            )}

            {successMsg && (
              <Alert severity="success" sx={{ mb: 3 }}>
                {successMsg}
              </Alert>
            )}

            {/* TAB 0: LOGIN */}
            {tabIndex === 0 && (
              <Box component="form" onSubmit={handleLoginSubmit(onLogin)} noValidate>
                <Stack spacing={2.5}>
                  <TextField
                    id="login-email"
                    label="Email Address"
                    fullWidth
                    autoComplete="email"
                    {...loginRegister('email')}
                    error={!!loginErrors.email}
                    helperText={loginErrors.email?.message}
                  />

                  <TextField
                    id="login-password"
                    label="Password"
                    type="password"
                    fullWidth
                    autoComplete="current-password"
                    {...loginRegister('password')}
                    error={!!loginErrors.password}
                    helperText={loginErrors.password?.message}
                  />

                  <Button
                    id="login-submit-button"
                    type="submit"
                    variant="contained"
                    size="large"
                    fullWidth
                    disabled={isLoggingIn}
                    sx={{ py: 1.3, mt: 1 }}
                  >
                    {isLoggingIn ? <CircularProgress size={24} color="inherit" /> : 'Sign In'}
                  </Button>
                </Stack>
              </Box>
            )}

            {/* TAB 1: REGISTER */}
            {tabIndex === 1 && (
              <Box component="form" onSubmit={handleRegSubmit(onRegister)} noValidate>
                <Stack spacing={2.5}>
                  <TextField
                    id="register-fullname"
                    label="Full Name"
                    fullWidth
                    autoComplete="name"
                    {...regRegister('fullName')}
                    error={!!regErrors.fullName}
                    helperText={regErrors.fullName?.message}
                  />

                  <TextField
                    id="register-email"
                    label="Email Address"
                    fullWidth
                    autoComplete="email"
                    {...regRegister('email')}
                    error={!!regErrors.email}
                    helperText={regErrors.email?.message}
                  />

                  <TextField
                    id="register-password"
                    label="Password"
                    type="password"
                    fullWidth
                    autoComplete="new-password"
                    {...regRegister('password')}
                    error={!!regErrors.password}
                    helperText={regErrors.password?.message}
                  />

                  <Button
                    id="register-submit-button"
                    type="submit"
                    variant="contained"
                    size="large"
                    fullWidth
                    disabled={isRegistering}
                    sx={{ py: 1.3, mt: 1 }}
                  >
                    {isRegistering ? <CircularProgress size={24} color="inherit" /> : 'Create Account'}
                  </Button>
                </Stack>
              </Box>
            )}
          </Box>
        </Paper>
      )}
    </Container>
  );
};

export default AuthPage;
