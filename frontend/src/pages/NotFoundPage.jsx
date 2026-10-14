import React from 'react';
import { Container, Typography, Button, Box } from '@mui/material';
import { Link } from 'react-router-dom';

export const NotFoundPage = () => {
  return (
    <Container maxWidth="sm" sx={{ textAlign: 'center', py: 8 }}>
      <Typography variant="h1" sx={{ fontWeight: 800, color: 'primary.main', mb: 2 }}>
        404
      </Typography>
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 600 }}>
        Page Not Found
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        The page you are looking for does not exist or has been moved.
      </Typography>
      <Button variant="contained" component={Link} to="/">
        Return Home
      </Button>
    </Container>
  );
};

export default NotFoundPage;
