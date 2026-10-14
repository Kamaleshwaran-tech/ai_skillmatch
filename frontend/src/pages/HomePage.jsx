import React from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Stack,
  Button,
} from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import StorageIcon from '@mui/icons-material/Storage';
import PsychologyIcon from '@mui/icons-material/Psychology';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import DescriptionIcon from '@mui/icons-material/Description';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import { useHealth } from '../hooks/useHealth';

export const HomePage = () => {
  const { data: healthData, isLoading, isError, error } = useHealth();

  const coreModules = [
    {
      title: 'Resume Parsing & Extraction',
      description: 'Upload resumes in PDF/DOCX format to extract structured experience and skill profiles.',
      icon: <DescriptionIcon color="primary" fontSize="large" />,
      tag: 'NLP Pipeline',
    },
    {
      title: 'Skill Taxonomy & Semantic Match',
      description: 'Standardize skills against a formal ontology and execute semantic similarity scoring.',
      icon: <PsychologyIcon color="secondary" fontSize="large" />,
      tag: 'Sentence Transformers',
    },
    {
      title: 'Real-Time Market Demand',
      description: 'Query live market demand data from Adzuna API to map current hiring trends.',
      icon: <TrendingUpIcon color="success" fontSize="large" />,
      tag: 'External Telemetry',
    },
    {
      title: 'Skill Gap & Pathway Generator',
      description: 'Identify critical missing competencies and generate customized learning roadmaps.',
      icon: <CompareArrowsIcon color="warning" fontSize="large" />,
      tag: 'Analytics Engine',
    },
  ];

  return (
    <Container maxWidth="lg">
      {/* Hero Section */}
      <Box sx={{ textAlign: 'center', my: 6 }}>
        <Chip
          label="Next-Gen Career Intelligence"
          color="primary"
          variant="filled"
          sx={{ mb: 2, fontWeight: 600 }}
        />
        <Typography
          variant="h2"
          component="h1"
          gutterBottom
          sx={{ fontWeight: 800, letterSpacing: '-1px' }}
        >
          SkillSync AI
        </Typography>
        <Typography
          variant="h5"
          color="text.secondary"
          sx={{ maxWidth: 720, mx: 'auto', mb: 4, lineHeight: 1.6 }}
        >
          Intelligent Skill Gap Analyzer & Market-Driven Career Pathway Generator
        </Typography>

        {/* Backend Live Status Banner */}
        <Box sx={{ maxWidth: 640, mx: 'auto', mb: 4 }}>
          {isLoading ? (
            <Card variant="outlined" sx={{ p: 2 }}>
              <Stack direction="row" spacing={2} alignItems="center" justifyContent="center">
                <CircularProgress size={24} />
                <Typography variant="body2" color="text.secondary">
                  Connecting to SkillSync AI Backend API...
                </Typography>
              </Stack>
            </Card>
          ) : isError ? (
            <Alert severity="warning">
              Backend not reachable yet ({error?.message || 'Check connection'}). Ensure backend is running at http://localhost:8000.
            </Alert>
          ) : (
            <Card variant="outlined" sx={{ bgcolor: '#ecfdf5', borderColor: '#a7f3d0' }}>
              <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
                <Stack direction="row" spacing={1.5} alignItems="center" justifyContent="center">
                  <CheckCircleOutlineIcon color="success" />
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#065f46' }}>
                    Backend Live: {healthData?.app} ({healthData?.status})
                  </Typography>
                  <Chip
                    size="small"
                    icon={<StorageIcon />}
                    label={`DB Dialect: ${healthData?.database?.dialect || 'sqlite'}`}
                    sx={{ bgcolor: '#d1fae5', color: '#065f46' }}
                  />
                </Stack>
              </CardContent>
            </Card>
          )}
        </Box>
      </Box>

      {/* Modules Overview */}
      <Box sx={{ mb: 6 }} id="features">
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 3, textAlign: 'center' }}>
          Platform Architecture & Modules
        </Typography>
        <Grid container spacing={3}>
          {coreModules.map((module) => (
            <Grid item xs={12} sm={6} md={6} key={module.title}>
              <Card
                variant="outlined"
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'box-shadow 0.2s ease',
                  '&:hover': { boxShadow: 3 },
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    {module.icon}
                    <Chip label={module.tag} size="small" variant="outlined" />
                  </Box>
                  <Typography variant="h6" component="h2" gutterBottom sx={{ fontWeight: 600 }}>
                    {module.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {module.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Architecture Highlights */}
      <Box
        id="architecture"
        sx={{
          bgcolor: 'background.paper',
          p: 4,
          borderRadius: 3,
          border: '1px solid #e2e8f0',
          mb: 6,
        }}
      >
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
          System Foundations
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          SkillSync AI is architected with a decoupled frontend (React + Material UI + TanStack Query) and a resilient backend (FastAPI + Pydantic v2 + SQLAlchemy 2.0).
        </Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 2 }}>
          <Button variant="outlined" href="/docs" target="_blank">
            FastAPI Swagger Docs
          </Button>
          <Button variant="outlined" href="/api/health" target="_blank">
            GET /api/health
          </Button>
        </Stack>
      </Box>
    </Container>
  );
};

export default HomePage;
