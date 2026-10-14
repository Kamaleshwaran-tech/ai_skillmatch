import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import MainLayout from './layouts/MainLayout';
import HomePage from './pages/HomePage';
import AuthPage from './pages/AuthPage';
import MarketDemandPage from './pages/MarketDemandPage';
import SkillGapPage from './pages/SkillGapPage';
import RoadmapPage from './pages/RoadmapPage';
import NotFoundPage from './pages/NotFoundPage';
import { AuthProvider } from './hooks/useAuth';

// Initialize React Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});

// Create customized MUI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#2563eb', // Modern indigo/blue
      light: '#60a5fa',
      dark: '#1d4ed8',
    },
    secondary: {
      main: '#7c3aed', // Purple accent
    },
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <BrowserRouter>
            <MainLayout>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/auth" element={<AuthPage />} />
                <Route path="/market-demand" element={<MarketDemandPage />} />
                <Route path="/skill-gap" element={<SkillGapPage />} />
                <Route path="/roadmap" element={<RoadmapPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </MainLayout>
          </BrowserRouter>
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
