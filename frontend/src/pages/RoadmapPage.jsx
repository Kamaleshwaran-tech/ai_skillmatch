import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  CircularProgress,
  Stack,
  Chip,
} from '@mui/material';
import RouteIcon from '@mui/icons-material/Route';
import DescriptionIcon from '@mui/icons-material/Description';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { fetchActiveResume, fetchLearningRoadmap } from '../services/skillGapService';
import SampleDataBanner from '../components/SampleDataBanner';
import LearningRoadmapView from '../components/LearningRoadmapView';

export const RoadmapPage = () => {
  const { isAuthenticated } = useAuth();
  const [activeResume, setActiveResume] = useState(null);
  const [isCheckingResume, setIsCheckingResume] = useState(false);

  const [targetRole, setTargetRole] = useState('Developer');
  const [targetLocation, setTargetLocation] = useState('San Francisco, CA');
  const [roadmapStatus, setRoadmapStatus] = useState('idle');
  const [roadmapError, setRoadmapError] = useState('');
  const [roadmapResult, setRoadmapResult] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) {
      setActiveResume(null);
      setRoadmapResult(null);
      return;
    }

    let isMounted = true;
    const loadActive = async () => {
      setIsCheckingResume(true);
      try {
        const data = await fetchActiveResume();
        if (!isMounted) return;
        if (data?.has_active_resume && data.resume) {
          setActiveResume(data.resume);
          if (data.latest_analysis?.target_role) {
            setTargetRole(data.latest_analysis.target_role);
          }
          if (data.latest_analysis?.target_location !== undefined) {
            setTargetLocation(data.latest_analysis.target_location || '');
          }
        } else {
          setActiveResume(null);
        }
      } catch {
        setActiveResume(null);
      } finally {
        if (isMounted) setIsCheckingResume(false);
      }
    };

    loadActive();
    return () => {
      isMounted = false;
    };
  }, [isAuthenticated]);

  const handleGenerateRoadmap = async () => {
    if (!activeResume) return;
    setRoadmapStatus('loading');
    setRoadmapError('');
    try {
      const params = {
        resume_id: activeResume.id,
        target_role: (targetRole || 'Developer').trim(),
        limit: 15,
      };
      if (targetLocation && targetLocation.trim()) {
        params.target_location = targetLocation.trim();
      }
      const data = await fetchLearningRoadmap(params);
      setRoadmapResult(data);
      setRoadmapStatus('success');
    } catch (err) {
      setRoadmapStatus('error');
      setRoadmapError(err.response?.data?.detail || 'Failed to generate learning roadmap.');
    }
  };

  if (!isAuthenticated) {
    return (
      <Container maxWidth="sm" sx={{ py: 8, textAlign: 'center' }}>
        <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
          <DescriptionIcon color="primary" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
            Authentication Required
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Please log in or register to generate a personalized learning roadmap from your active resume.
          </Typography>
          <Button variant="contained" component={Link} to="/auth">
            Sign In / Register
          </Button>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'flex-start', sm: 'center' }}
          spacing={1.5}
          sx={{ mb: 1 }}
        >
          <Stack direction="row" spacing={1.5} alignItems="center">
            <RouteIcon color="primary" sx={{ fontSize: 36 }} />
            <Typography variant="h4" sx={{ fontWeight: 800 }}>
              Role Learning Roadmap
            </Typography>
          </Stack>
          {activeResume && (
            <Chip
              label={`Active Resume: ${activeResume.filename} (${activeResume.extracted_skills_count} skills)`}
              color="success"
              variant="outlined"
              sx={{ fontWeight: 600 }}
            />
          )}
        </Stack>
        <Typography variant="body1" color="text.secondary">
          Market-driven learning sequence ordered by real skill demand percentages, with AI-generated guidance and general learning resource suggestions.
        </Typography>
      </Box>

      {roadmapResult && (
        <SampleDataBanner
          isSampleData={roadmapResult.is_sample_data}
          message={roadmapResult.banner_message}
        />
      )}

      {isCheckingResume ? (
        <Paper elevation={1} sx={{ p: 6, textAlign: 'center', borderRadius: 2.5 }}>
          <CircularProgress size={36} sx={{ mb: 2 }} />
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            Loading your active resume...
          </Typography>
        </Paper>
      ) : !activeResume ? (
        <Paper
          elevation={1}
          sx={{
            p: 6,
            textAlign: 'center',
            borderRadius: 2.5,
            bgcolor: '#f8fafc',
            border: '1px dashed #cbd5e1',
          }}
        >
          <DescriptionIcon sx={{ fontSize: 56, color: '#94a3b8', mb: 2 }} />
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 1, color: '#334155' }}>
            No Active Resume Found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 460, mx: 'auto', mb: 3 }}>
            Please upload a resume on the Skill Gap Analysis page first so we can identify your current skills and build a personalized roadmap.
          </Typography>
          <Button variant="contained" component={Link} to="/skill-gap">
            Go to Upload Resume
          </Button>
        </Paper>
      ) : (
        <LearningRoadmapView
          targetRole={targetRole}
          setTargetRole={setTargetRole}
          targetLocation={targetLocation}
          setTargetLocation={setTargetLocation}
          onGenerateRoadmap={handleGenerateRoadmap}
          roadmapStatus={roadmapStatus}
          roadmapError={roadmapError}
          roadmapResult={roadmapResult}
          disabled={!activeResume}
        />
      )}
    </Container>
  );
};

export default RoadmapPage;
