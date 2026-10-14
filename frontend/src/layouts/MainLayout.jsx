import React from 'react';
import { Box } from '@mui/material';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export const MainLayout = ({ children }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: '#f8fafc' }}>
      <Navbar />
      <Box component="main" sx={{ flexGrow: 1, py: 4 }}>
        {children}
      </Box>
      <Footer />
    </Box>
  );
};

export default MainLayout;
