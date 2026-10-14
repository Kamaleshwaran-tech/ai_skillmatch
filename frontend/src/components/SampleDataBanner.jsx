import React from 'react';
import { Alert, Box } from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

export const SampleDataBanner = ({ isSampleData, message }) => {
  if (!isSampleData) return null;

  return (
    <Box sx={{ mb: 3 }} id="sample-data-banner">
      <Alert
        severity="warning"
        icon={<InfoOutlinedIcon fontSize="inherit" />}
        sx={{
          bgcolor: '#fffbeb',
          color: '#b45309',
          border: '1px solid #fde68a',
          fontWeight: 600,
        }}
      >
        {message || 'SAMPLE DATA — not live (Adzuna credentials not configured or live API offline)'}
      </Alert>
    </Box>
  );
};

export default SampleDataBanner;
