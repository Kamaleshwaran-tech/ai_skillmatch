import React from 'react';
import { Box, Typography, Container, Divider } from '@mui/material';
import { APP_NAME } from '../utils/constants';

export const Footer = () => {
  return (
    <Box component="footer" sx={{ bgcolor: 'background.paper', py: 4, mt: 'auto' }}>
      <Divider sx={{ mb: 3 }} />
      <Container maxWidth="lg">
        <Typography variant="body2" color="text.secondary" align="center">
          © {new Date().getFullYear()} {APP_NAME}. Intelligent Skill Gap Analyzer & Market-Driven Career Pathway Generator.
        </Typography>
      </Container>
    </Box>
  );
};

export default Footer;
