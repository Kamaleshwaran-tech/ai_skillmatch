import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Chip,
  Stack,
  Divider,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Tabs,
  Tab,
  Skeleton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Snackbar,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import DescriptionIcon from '@mui/icons-material/Description';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import WorkOutlineIcon from '@mui/icons-material/WorkOutline';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import RefreshIcon from '@mui/icons-material/Refresh';
import HistoryIcon from '@mui/icons-material/History';
import RouteIcon from '@mui/icons-material/Route';

import {
  uploadResumeFile,
  fetchActiveResume,
  fetchUserResumes,
  activateResume,
  analyzeSkillGap,
  fetchJobRecommendations,
  fetchLearningRoadmap,
} from '../services/skillGapService';
import SampleDataBanner from '../components/SampleDataBanner';
import RecommendedJobCard from '../components/RecommendedJobCard';
import LearningRoadmapView from '../components/LearningRoadmapView';
import { useAuth } from '../hooks/useAuth';
import { Link } from 'react-router-dom';

export const SkillGapPage = () => {
  const { isAuthenticated, refetchActiveResume } = useAuth();

  // Tab State: 0 = Recommended Jobs, 1 = Skill Gap Analysis, 2 = Learning Roadmap
  const [activeTab, setActiveTab] = useState(0);

  // Resume Upload & Active Persistence State
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('idle'); // 'idle' | 'uploading' | 'success' | 'error'
  const [uploadError, setUploadError] = useState('');
  const [uploadedResume, setUploadedResume] = useState(null);
  const [isCheckingActive, setIsCheckingActive] = useState(false);
  const [resumeHistory, setResumeHistory] = useState([]);
  const [replacementNotice, setReplacementNotice] = useState('');
  const [toastOpen, setToastOpen] = useState(false);

  // Recommended Jobs State
  const [jobRecs, setJobRecs] = useState(null);
  const [jobRecsStatus, setJobRecsStatus] = useState('idle'); // 'idle' | 'loading' | 'success' | 'error'
  const [jobRecsError, setJobRecsError] = useState('');
  const [recsLocationFilter, setRecsLocationFilter] = useState('');
  const [minMatchFilter, setMinMatchFilter] = useState(0);

  // Role Skill Gap Analysis State
  const [targetRole, setTargetRole] = useState('Developer');
  const [targetLocation, setTargetLocation] = useState('San Francisco, CA');
  const [analysisStatus, setAnalysisStatus] = useState('idle'); // 'idle' | 'analyzing' | 'success' | 'error'
  const [analysisError, setAnalysisError] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);

  // Learning Roadmap State
  const [roadmapStatus, setRoadmapStatus] = useState('idle'); // 'idle' | 'loading' | 'success' | 'error'
  const [roadmapError, setRoadmapError] = useState('');
  const [roadmapResult, setRoadmapResult] = useState(null);

  const loadJobRecommendations = async (resumeId, loc = recsLocationFilter, minMatch = minMatchFilter) => {
    if (!resumeId) return;
    setJobRecsStatus('loading');
    setJobRecsError('');
    try {
      const params = {
        resume_id: resumeId,
        limit: 20,
      };
      if (loc && loc.trim()) params.location = loc.trim();
      if (minMatch > 0) params.min_match = minMatch;

      const data = await fetchJobRecommendations(params);
      setJobRecs(data);
      setJobRecsStatus('success');
    } catch (err) {
      setJobRecsStatus('error');
      setJobRecsError(err.response?.data?.detail || 'Failed to load job recommendations.');
    }
  };

  const runSkillGapForResume = async (resumeId, role = targetRole, loc = targetLocation, switchTab = false) => {
    if (!resumeId) return;
    setAnalysisStatus('analyzing');
    setAnalysisError('');
    try {
      const payload = {
        resume_id: resumeId,
        target_role: (role || 'Developer').trim(),
        target_location: (loc || '').trim(),
        limit: 15,
      };
      const result = await analyzeSkillGap(payload);
      setAnalysisResult(result);
      setAnalysisStatus('success');
      if (switchTab) {
        setActiveTab(1);
      }
    } catch (err) {
      setAnalysisStatus('error');
      setAnalysisError(err.response?.data?.detail || 'Skill gap analysis failed.');
    }
  };

  const loadResumeHistoryList = async () => {
    try {
      const listData = await fetchUserResumes();
      setResumeHistory(listData.resumes || []);
    } catch {
      // Non-blocking if history fetch fails
    }
  };

  // Automatically load active resume, skill-gap analysis, and job recommendations on login / page load
  useEffect(() => {
    if (!isAuthenticated) {
      setUploadedResume(null);
      setJobRecs(null);
      setAnalysisResult(null);
      setResumeHistory([]);
      setReplacementNotice('');
      return;
    }

    let isMounted = true;
    const initActiveResume = async () => {
      setIsCheckingActive(true);
      try {
        const [activeData, listData] = await Promise.all([
          fetchActiveResume(),
          fetchUserResumes(),
        ]);
        if (!isMounted) return;

        setResumeHistory(listData?.resumes || []);

        if (activeData?.has_active_resume && activeData.resume) {
          setUploadedResume(activeData.resume);
          // Populate job recommendations immediately
          loadJobRecommendations(activeData.resume.id, '', 0);

          // Populate skill-gap analysis from persisted latest_analysis or run automatically
          if (activeData.latest_analysis) {
            setAnalysisResult(activeData.latest_analysis);
            setAnalysisStatus('success');
            if (activeData.latest_analysis.target_role) {
              setTargetRole(activeData.latest_analysis.target_role);
            }
            if (activeData.latest_analysis.target_location !== undefined) {
              setTargetLocation(activeData.latest_analysis.target_location || '');
            }
          } else {
            runSkillGapForResume(activeData.resume.id, targetRole, targetLocation, false);
          }
        } else {
          setUploadedResume(null);
        }
      } catch {
        // Keep upload prompt visible if no active resume
      } finally {
        if (isMounted) {
          setIsCheckingActive(false);
        }
      }
    };

    initActiveResume();
    return () => {
      isMounted = false;
    };
  }, [isAuthenticated]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadStatus('idle');
      setUploadError('');
    }
  };

  const handleUploadResume = async () => {
    if (!file) return;
    setUploadStatus('uploading');
    setUploadError('');
    setReplacementNotice('');
    try {
      const result = await uploadResumeFile(file);
      setUploadedResume(result);
      setUploadStatus('success');

      if (result.replaced_previous) {
        const msg = 'New resume set as active — previous resume kept in your history';
        setReplacementNotice(msg);
        setToastOpen(true);
      }

      // Refresh resume history and auth context active resume
      await loadResumeHistoryList();
      if (refetchActiveResume) refetchActiveResume();

      // Refresh dashboard (job recommendations & skill-gap results) from the new active resume
      setActiveTab(0);
      loadJobRecommendations(result.id);
      runSkillGapForResume(result.id, targetRole, targetLocation, false);
    } catch (err) {
      setUploadStatus('error');
      setUploadError(err.response?.data?.detail || 'Failed to upload resume.');
    }
  };

  const handleSwitchActiveResume = async (resumeId) => {
    try {
      const activated = await activateResume(resumeId);
      if (activated?.has_active_resume && activated.resume) {
        setUploadedResume(activated.resume);
        setReplacementNotice(`Switched active resume to ${activated.resume.filename} — all resumes kept in history`);
        setToastOpen(true);
        await loadResumeHistoryList();
        if (refetchActiveResume) refetchActiveResume();
        loadJobRecommendations(activated.resume.id);
        if (activated.latest_analysis) {
          setAnalysisResult(activated.latest_analysis);
          setAnalysisStatus('success');
        } else {
          runSkillGapForResume(activated.resume.id, targetRole, targetLocation, false);
        }
      }
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Failed to switch active resume.');
    }
  };

  const handleRunAnalysis = async () => {
    if (!uploadedResume) return;
    await runSkillGapForResume(uploadedResume.id, targetRole, targetLocation, true);
  };

  const handleGenerateRoadmap = async (switchTab = true) => {
    if (!uploadedResume) return;
    setRoadmapStatus('loading');
    setRoadmapError('');
    if (switchTab) {
      setActiveTab(2);
    }
    try {
      const params = {
        resume_id: uploadedResume.id,
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

  const getPriorityChip = (priority) => {
    let color = 'default';
    if (priority === 'High') color = 'error';
    else if (priority === 'Medium') color = 'warning';
    else if (priority === 'Low') color = 'info';

    return <Chip label={`Priority: ${priority}`} size="small" color={color} sx={{ fontWeight: 600 }} />;
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
            Please log in or register to upload resumes, discover matched jobs, and perform skill gap analyses.
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
      {/* Toast Notification for Replaced Resume */}
      <Snackbar
        open={toastOpen}
        autoHideDuration={6000}
        onClose={() => setToastOpen(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setToastOpen(false)}
          severity="info"
          variant="filled"
          sx={{ width: '100%', fontWeight: 600 }}
        >
          {replacementNotice}
        </Alert>
      </Snackbar>

      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 1 }}>
          <CompareArrowsIcon color="primary" sx={{ fontSize: 36 }} />
          <Typography variant="h4" sx={{ fontWeight: 800 }}>
            Skill Gap Analyzer & Career Pathway Engine
          </Typography>
        </Stack>
        <Typography variant="body1" color="text.secondary">
          Upload your resume to discover real job recommendations tailored to your skills and identify critical career gaps.
        </Typography>
      </Box>

      {/* Replacement Banner (Persisted on page when a new resume replaces a previous active resume) */}
      {replacementNotice && (
        <Alert
          severity="info"
          id="resume-replaced-alert"
          sx={{ mb: 3, fontWeight: 600 }}
          onClose={() => setReplacementNotice('')}
        >
          {replacementNotice}
        </Alert>
      )}

      {/* Top Banner (Shows if active tab reports sample fixtures) */}
      {activeTab === 0 && jobRecs && (
        <SampleDataBanner
          isSampleData={jobRecs.is_sample_data}
          message={jobRecs.banner_message}
        />
      )}
      {activeTab === 1 && analysisResult && (
        <SampleDataBanner
          isSampleData={analysisResult.is_sample_data}
          message={analysisResult.banner_message}
        />
      )}
      {activeTab === 2 && roadmapResult && (
        <SampleDataBanner
          isSampleData={roadmapResult.is_sample_data}
          message={roadmapResult.banner_message}
        />
      )}

      <Grid container spacing={4}>
        {/* Left Column: Upload Resume, History & Target Role Forms */}
        <Grid item xs={12} md={4}>
          {/* Step 1: Upload Resume Card */}
          <Paper elevation={2} sx={{ p: 3, borderRadius: 2, mb: 3 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                Step 1: {uploadedResume ? 'Active Resume' : 'Upload Resume'}
              </Typography>
              {uploadedResume && (
                <Chip
                  id="active-resume-chip"
                  label="Active"
                  color="success"
                  size="small"
                  sx={{ fontWeight: 700 }}
                />
              )}
            </Stack>

            <Box
              sx={{
                border: '2px dashed #cbd5e1',
                borderRadius: 2,
                p: 3,
                textAlign: 'center',
                bgcolor: '#f8fafc',
                cursor: 'pointer',
                mb: 2,
              }}
            >
              <input
                id="resume-file-input"
                type="file"
                accept=".pdf,.docx"
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
              <label htmlFor="resume-file-input" style={{ cursor: 'pointer' }}>
                <CloudUploadIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  {file ? file.name : 'Click to select PDF or DOCX file'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {uploadedResume
                    ? 'Upload a new file to replace your current active resume'
                    : 'PyMuPDF text extraction & verified skill normalization'}
                </Typography>
              </label>
            </Box>

            <Button
              id="upload-resume-button"
              variant="contained"
              fullWidth
              disabled={!file || uploadStatus === 'uploading'}
              onClick={handleUploadResume}
              startIcon={uploadStatus === 'uploading' ? <CircularProgress size={18} color="inherit" /> : <CloudUploadIcon />}
            >
              {uploadStatus === 'uploading' ? 'Extracting Skills...' : 'Upload & Parse Resume'}
            </Button>

            {uploadStatus === 'error' && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {uploadError}
              </Alert>
            )}

            {uploadedResume && (
              <Alert severity="success" sx={{ mt: 2 }} id="upload-success-alert">
                <Typography variant="subtitle2" sx={{ fontWeight: 700 }} id="active-resume-filename">
                  {uploadedResume.filename} (Active)
                </Typography>
                <Typography variant="caption" display="block">
                  {uploadedResume.extracted_skills_count} skills extracted • ID #{uploadedResume.id}
                </Typography>
              </Alert>
            )}
          </Paper>

          {/* Resume History Card (GET /api/resumes) */}
          {resumeHistory.length > 0 && (
            <Paper elevation={2} sx={{ p: 3, borderRadius: 2, mb: 3 }} id="resume-history-card">
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1.5 }}>
                <HistoryIcon color="primary" fontSize="small" />
                <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                  Resume History ({resumeHistory.length})
                </Typography>
              </Stack>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1.5 }}>
                Your active resume drives the dashboard. Past uploads are preserved in your history.
              </Typography>
              <Divider sx={{ mb: 1 }} />
              <List disablePadding id="resume-history-list">
                {resumeHistory.map((item) => (
                  <ListItem
                    key={item.id}
                    disableGutters
                    sx={{
                      py: 1,
                      px: 1,
                      mb: 0.5,
                      borderRadius: 1.5,
                      bgcolor: item.is_active ? '#f0fdf4' : 'transparent',
                      border: item.is_active ? '1px solid #bbf7d0' : '1px solid transparent',
                    }}
                    data-testid={`history-resume-item-${item.id}`}
                  >
                    <ListItemText
                      primary={
                        <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                          <Typography
                            variant="body2"
                            sx={{
                              fontWeight: item.is_active ? 700 : 500,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {item.filename}
                          </Typography>
                          {item.is_active ? (
                            <Chip
                              label="Active"
                              size="small"
                              color="success"
                              sx={{ height: 20, fontSize: '0.68rem', fontWeight: 700 }}
                            />
                          ) : (
                            <Button
                              size="small"
                              variant="text"
                              sx={{ fontSize: '0.7rem', minWidth: 'auto', py: 0, px: 1 }}
                              onClick={() => handleSwitchActiveResume(item.id)}
                            >
                              Set Active
                            </Button>
                          )}
                        </Stack>
                      }
                      secondary={
                        <Typography variant="caption" color="text.secondary">
                          {item.extracted_skills_count} skills • Uploaded{' '}
                          {new Date(item.created_at).toLocaleString()}
                        </Typography>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}

          {/* Step 2: Target Role & Analysis Form */}
          <Paper elevation={2} sx={{ p: 3, borderRadius: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
              Step 2: Role Skill Gap & Roadmap
            </Typography>

            <Stack spacing={2}>
              <TextField
                id="target-role-input"
                label="Target Job Role / Stack"
                placeholder="e.g. Developer, Python, React"
                fullWidth
                size="small"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
              />

              <TextField
                id="target-location-input"
                label="Target Location (Optional)"
                placeholder="e.g. San Francisco, CA or Remote"
                fullWidth
                size="small"
                value={targetLocation}
                onChange={(e) => setTargetLocation(e.target.value)}
              />

              <Button
                id="run-analysis-button"
                variant="contained"
                color="secondary"
                size="large"
                fullWidth
                disabled={!uploadedResume || analysisStatus === 'analyzing'}
                onClick={handleRunAnalysis}
                startIcon={analysisStatus === 'analyzing' ? <CircularProgress size={20} color="inherit" /> : <PlayArrowIcon />}
              >
                {analysisStatus === 'analyzing' ? 'Comparing Embeddings...' : 'Analyze Role Skill Gap'}
              </Button>

              <Button
                id="sidebar-generate-roadmap-button"
                variant="outlined"
                color="primary"
                size="large"
                fullWidth
                disabled={!uploadedResume || roadmapStatus === 'loading'}
                onClick={() => handleGenerateRoadmap(true)}
                startIcon={roadmapStatus === 'loading' ? <CircularProgress size={20} color="inherit" /> : <RouteIcon />}
              >
                {roadmapStatus === 'loading' ? 'Generating Roadmap...' : 'Generate Learning Roadmap'}
              </Button>
            </Stack>

            {analysisStatus === 'error' && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {analysisError}
              </Alert>
            )}
          </Paper>
        </Grid>

        {/* Right Column: Interactive Tabs (Recommended Jobs, Skill Gap Analysis & Learning Roadmap) */}
        <Grid item xs={12} md={8}>
          {isCheckingActive && !uploadedResume ? (
            <Paper elevation={1} sx={{ p: 6, textAlign: 'center', borderRadius: 2.5 }}>
              <CircularProgress size={36} sx={{ mb: 2 }} />
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Checking for your active resume...
              </Typography>
            </Paper>
          ) : !uploadedResume ? (
            <Paper
              elevation={1}
              sx={{
                p: 6,
                textAlign: 'center',
                borderRadius: 2.5,
                bgcolor: '#f8fafc',
                border: '1px dashed #cbd5e1',
              }}
              id="no-active-resume-prompt"
            >
              <WorkOutlineIcon sx={{ fontSize: 56, color: '#94a3b8', mb: 2 }} />
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1, color: '#334155' }}>
                No Resume Uploaded Yet
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 460, mx: 'auto' }}>
                Upload your resume in Step 1 to instantly see job recommendations ranked by match percentage and explore skill gap insights.
              </Typography>
            </Paper>
          ) : (
            <Box>
              {/* Tabs Navigation */}
              <Paper elevation={1} sx={{ borderRadius: 2, mb: 3 }}>
                <Tabs
                  value={activeTab}
                  onChange={(e, newVal) => setActiveTab(newVal)}
                  variant="fullWidth"
                  indicatorColor="primary"
                  textColor="primary"
                >
                  <Tab
                    id="tab-recommended-jobs"
                    icon={<WorkOutlineIcon />}
                    iconPosition="start"
                    label={`Recommended Jobs ${jobRecs?.recommendations?.length ? `(${jobRecs.recommendations.length})` : ''}`}
                    sx={{ fontWeight: 700, textTransform: 'none', py: 1.5 }}
                  />
                  <Tab
                    id="tab-skill-gap"
                    icon={<CompareArrowsIcon />}
                    iconPosition="start"
                    label="Role Skill Gap Analysis"
                    sx={{ fontWeight: 700, textTransform: 'none', py: 1.5 }}
                  />
                  <Tab
                    id="tab-learning-roadmap"
                    icon={<RouteIcon />}
                    iconPosition="start"
                    label="Learning Roadmap"
                    sx={{ fontWeight: 700, textTransform: 'none', py: 1.5 }}
                  />
                </Tabs>
              </Paper>

              {/* TAB 0: RECOMMENDED JOBS */}
              {activeTab === 0 && (
                <Box id="recommended-jobs-tab-content">
                  {/* Filter and Ranking Header Bar */}
                  <Paper variant="outlined" sx={{ p: 2, mb: 3, borderRadius: 2, bgcolor: '#ffffff' }}>
                    <Stack
                      direction={{ xs: 'column', sm: 'row' }}
                      justifyContent="space-between"
                      alignItems={{ xs: 'flex-start', sm: 'center' }}
                      spacing={2}
                    >
                      {/* Sort Indicator */}
                      <Stack direction="row" spacing={1} alignItems="center">
                        <TrendingUpIcon color="primary" />
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                            Ranked by Skill Match %
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Ordered descending (highest match first)
                          </Typography>
                        </Box>
                      </Stack>

                      {/* Filter Controls */}
                      <Stack direction="row" spacing={1.5} alignItems="center" sx={{ width: { xs: '100%', sm: 'auto' } }}>
                        <TextField
                          size="small"
                          placeholder="Filter location..."
                          value={recsLocationFilter}
                          onChange={(e) => setRecsLocationFilter(e.target.value)}
                          sx={{ width: { xs: '100%', sm: 160 } }}
                        />

                        <FormControl size="small" sx={{ minWidth: 120 }}>
                          <InputLabel id="min-match-label">Min Match</InputLabel>
                          <Select
                            labelId="min-match-label"
                            label="Min Match"
                            value={minMatchFilter}
                            onChange={(e) => setMinMatchFilter(Number(e.target.value))}
                          >
                            <MenuItem value={0}>All matches</MenuItem>
                            <MenuItem value={30}>≥ 30%</MenuItem>
                            <MenuItem value={50}>≥ 50%</MenuItem>
                            <MenuItem value={70}>≥ 70%</MenuItem>
                          </Select>
                        </FormControl>

                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => loadJobRecommendations(uploadedResume.id, recsLocationFilter, minMatchFilter)}
                          startIcon={<RefreshIcon />}
                          disabled={jobRecsStatus === 'loading'}
                        >
                          Filter
                        </Button>
                      </Stack>
                    </Stack>

                    {/* Resume Top Skills Used */}
                    {jobRecs?.top_resume_skills && jobRecs.top_resume_skills.length > 0 && (
                      <Box sx={{ mt: 1.5, pt: 1.5, borderTop: '1px solid #f1f5f9' }}>
                        <Typography variant="caption" color="text.secondary" sx={{ mr: 1, fontWeight: 600 }}>
                          Skills Matched:
                        </Typography>
                        {jobRecs.top_resume_skills.map((s, idx) => (
                          <Chip
                            key={idx}
                            label={s}
                            size="small"
                            variant="outlined"
                            color="primary"
                            sx={{ mr: 0.5, mb: 0.5, fontSize: '0.7rem' }}
                          />
                        ))}
                      </Box>
                    )}
                  </Paper>

                  {/* Loading Skeletons */}
                  {jobRecsStatus === 'loading' && (
                    <Grid container spacing={3} id="job-recommendations-loading">
                      {[1, 2, 3, 4].map((n) => (
                        <Grid item xs={12} sm={12} md={6} key={n}>
                          <Paper variant="outlined" sx={{ p: 2.5, borderRadius: 2.5 }}>
                            <Stack direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
                              <Box sx={{ width: '70%' }}>
                                <Skeleton variant="text" height={28} width="90%" />
                                <Skeleton variant="text" height={20} width="60%" />
                              </Box>
                              <Skeleton variant="rounded" width={60} height={40} />
                            </Stack>
                            <Skeleton variant="rectangular" height={6} sx={{ borderRadius: 3, mb: 2 }} />
                            <Skeleton variant="text" height={20} width="40%" sx={{ mb: 2 }} />
                            <Skeleton variant="rectangular" height={45} sx={{ borderRadius: 1, mb: 2 }} />
                            <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                              <Skeleton variant="rounded" width={60} height={24} />
                              <Skeleton variant="rounded" width={70} height={24} />
                              <Skeleton variant="rounded" width={55} height={24} />
                            </Stack>
                            <Skeleton variant="rounded" height={36} />
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  )}

                  {/* Error State */}
                  {jobRecsStatus === 'error' && (
                    <Alert
                      severity="error"
                      sx={{ mb: 3 }}
                      action={
                        <Button color="inherit" size="small" onClick={() => loadJobRecommendations(uploadedResume.id)}>
                          Retry
                        </Button>
                      }
                    >
                      {jobRecsError}
                    </Alert>
                  )}

                  {/* Empty State */}
                  {jobRecsStatus === 'success' && jobRecs.recommendations.length === 0 && (
                    <Paper
                      variant="outlined"
                      sx={{
                        p: 5,
                        textAlign: 'center',
                        borderRadius: 2.5,
                        bgcolor: '#ffffff',
                      }}
                      id="job-recommendations-empty"
                    >
                      <WorkOutlineIcon sx={{ fontSize: 48, color: '#94a3b8', mb: 1.5 }} />
                      <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                        No Matching Job Listings Found
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 450, mx: 'auto', mb: 2 }}>
                        No active jobs meet your current filter criteria. Try clearing the location filter or lowering the minimum match percentage.
                      </Typography>
                      <Button
                        variant="outlined"
                        onClick={() => {
                          setRecsLocationFilter('');
                          setMinMatchFilter(0);
                          loadJobRecommendations(uploadedResume.id, '', 0);
                        }}
                      >
                        Reset Filters
                      </Button>
                    </Paper>
                  )}

                  {/* Recommendations Cards Grid (Responsive 2-column or stacked) */}
                  {jobRecsStatus === 'success' && jobRecs.recommendations.length > 0 && (
                    <Grid container spacing={3} id="job-recommendations-grid">
                      {jobRecs.recommendations.map((job) => (
                        <Grid item xs={12} sm={12} md={6} key={job.job_id}>
                          <RecommendedJobCard job={job} />
                        </Grid>
                      ))}
                    </Grid>
                  )}
                </Box>
              )}

              {/* TAB 1: ROLE SKILL GAP ANALYSIS */}
              {activeTab === 1 && (
                <Box id="skill-gap-tab-content">
                  {analysisStatus === 'analyzing' && (
                    <Paper elevation={2} sx={{ p: 6, textAlign: 'center', borderRadius: 2 }}>
                      <CircularProgress size={48} sx={{ mb: 2 }} />
                      <Typography variant="h6" sx={{ fontWeight: 700 }}>
                        Evaluating Skill Overlap
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Running 5-stage matcher: exact match $\rightarrow$ alias resolution $\rightarrow$ all-MiniLM-L6-v2 semantic comparison $\rightarrow$ evidence validation...
                      </Typography>
                    </Paper>
                  )}

                  {!analysisResult && analysisStatus !== 'analyzing' && (
                    <Paper variant="outlined" sx={{ p: 5, textAlign: 'center', borderRadius: 2.5, bgcolor: '#ffffff' }}>
                      <CompareArrowsIcon sx={{ fontSize: 48, color: '#94a3b8', mb: 1.5 }} />
                      <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                        No Analysis Generated Yet
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 450, mx: 'auto', mb: 2 }}>
                        Specify a target role and click <strong>Analyze Role Skill Gap</strong> in Step 2 to generate a detailed competency report.
                      </Typography>
                      <Button variant="contained" color="secondary" onClick={handleRunAnalysis}>
                        Analyze for "{targetRole}"
                      </Button>
                    </Paper>
                  )}

                  {analysisResult && (
                    <Stack spacing={3} id="skill-gap-results-panel">
                      {/* Match Summary Scorecard */}
                      <Card variant="outlined" sx={{ bgcolor: '#ffffff', borderRadius: 2 }}>
                        <CardContent>
                          <Typography variant="overline" color="text.secondary">
                            Analysis Results Overview
                          </Typography>
                          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                            <Typography variant="h5" sx={{ fontWeight: 800 }} id="skill-gap-overall-match-pct">
                              Competency Match: {analysisResult.summary.overall_match_percentage}%
                            </Typography>
                            <Chip
                              label={`${analysisResult.total_listings_analyzed} Unique Postings Analyzed`}
                              color="primary"
                              variant="outlined"
                            />
                          </Stack>
                          <LinearProgress
                            variant="determinate"
                            value={analysisResult.summary.overall_match_percentage}
                            sx={{ height: 10, borderRadius: 5, mb: 2 }}
                          />

                          <Grid container spacing={2} sx={{ textAlign: 'center' }}>
                            <Grid item xs={4}>
                              <Paper variant="outlined" sx={{ p: 1.5, bgcolor: '#f0fdf4' }}>
                                <Typography variant="h5" sx={{ fontWeight: 800, color: '#166534' }}>
                                  {analysisResult.summary.matched_count}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  Matched Skills
                                </Typography>
                              </Paper>
                            </Grid>
                            <Grid item xs={4}>
                              <Paper variant="outlined" sx={{ p: 1.5, bgcolor: '#fef2f2' }}>
                                <Typography variant="h5" sx={{ fontWeight: 800, color: '#991b1b' }}>
                                  {analysisResult.summary.missing_count}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  Missing Skills
                                </Typography>
                              </Paper>
                            </Grid>
                            <Grid item xs={4}>
                              <Paper variant="outlined" sx={{ p: 1.5, bgcolor: '#fffbeb' }}>
                                <Typography variant="h5" sx={{ fontWeight: 800, color: '#92400e' }}>
                                  {analysisResult.summary.needs_review_count}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  Needs Review
                                </Typography>
                              </Paper>
                            </Grid>
                          </Grid>
                        </CardContent>
                      </Card>

                      {/* Matched Skills List */}
                      <Paper elevation={1} sx={{ p: 3, borderRadius: 2 }}>
                        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
                          <CheckCircleIcon color="success" />
                          <Typography variant="h6" sx={{ fontWeight: 700 }}>
                            Matched Skills ({analysisResult.matched_skills.length})
                          </Typography>
                        </Stack>
                        {analysisResult.matched_skills.length === 0 ? (
                          <Typography variant="body2" color="text.secondary">No skills directly matched.</Typography>
                        ) : (
                          <List disablePadding>
                            {analysisResult.matched_skills.map((s, idx) => (
                              <ListItem key={idx} sx={{ px: 0, py: 1.5, borderBottom: '1px solid #f1f5f9' }}>
                                <ListItemText
                                  primary={
                                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                                      <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                                        {s.skill}
                                      </Typography>
                                      <Chip label={`Method: ${s.method}`} size="small" variant="outlined" />
                                      <Chip label={`Demand: ${s.demand_percentage}%`} size="small" color="primary" variant="outlined" />
                                      {getPriorityChip(s.priority)}
                                    </Stack>
                                  }
                                  secondary={
                                    <Box sx={{ mt: 0.5 }}>
                                      <Typography variant="body2" color="text.secondary">
                                        <em>Evidence:</em> "{s.evidence_text}"
                                      </Typography>
                                      <Typography variant="caption" color="text.secondary" display="block">
                                        {s.explanation}
                                      </Typography>
                                    </Box>
                                  }
                                />
                              </ListItem>
                            ))}
                          </List>
                        )}
                      </Paper>

                      {/* Missing Skills List */}
                      <Paper elevation={1} sx={{ p: 3, borderRadius: 2 }}>
                        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
                          <CancelIcon color="error" />
                          <Typography variant="h6" sx={{ fontWeight: 700 }}>
                            Missing Competencies ({analysisResult.missing_skills.length})
                          </Typography>
                        </Stack>
                        {analysisResult.missing_skills.length === 0 ? (
                          <Typography variant="body2" color="text.secondary">None! Your profile matches all demanded skills.</Typography>
                        ) : (
                          <List disablePadding>
                            {analysisResult.missing_skills.map((s, idx) => (
                              <ListItem key={idx} sx={{ px: 0, py: 1.5, borderBottom: '1px solid #f1f5f9' }}>
                                <ListItemText
                                  primary={
                                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                                      <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                                        {s.skill}
                                      </Typography>
                                      <Chip label={`Demand: ${s.demand_percentage}%`} size="small" color="error" variant="outlined" />
                                      <Chip label={`${s.matching_listings_count} of ${s.total_listings_analyzed} jobs`} size="small" variant="outlined" />
                                      {getPriorityChip(s.priority)}
                                    </Stack>
                                  }
                                  secondary={
                                    <Typography variant="caption" color="text.secondary" display="block">
                                      {s.explanation}
                                    </Typography>
                                  }
                                />
                              </ListItem>
                            ))}
                          </List>
                        )}
                      </Paper>

                      {/* Needs Review List */}
                      {analysisResult.needs_review_skills.length > 0 && (
                        <Paper elevation={1} sx={{ p: 3, borderRadius: 2, bgcolor: '#fffdf5' }}>
                          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
                            <HelpOutlineIcon color="warning" />
                            <Typography variant="h6" sx={{ fontWeight: 700 }}>
                              Needs Human Review ({analysisResult.needs_review_skills.length})
                            </Typography>
                          </Stack>
                          <List disablePadding>
                            {analysisResult.needs_review_skills.map((s, idx) => (
                              <ListItem key={idx} sx={{ px: 0, py: 1.5, borderBottom: '1px solid #fef3c7' }}>
                                <ListItemText
                                  primary={
                                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                                      <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                                        {s.skill}
                                      </Typography>
                                      <Chip label={`Sim Score: ${s.similarity_score}`} size="small" color="warning" />
                                      {getPriorityChip(s.priority)}
                                    </Stack>
                                  }
                                  secondary={
                                    <Box sx={{ mt: 0.5 }}>
                                      <Typography variant="body2" color="text.secondary">
                                        <em>Candidate mention:</em> "{s.matched_candidate_text}"
                                      </Typography>
                                      <Typography variant="caption" color="text.secondary" display="block">
                                        {s.explanation}
                                      </Typography>
                                    </Box>
                                  }
                                />
                              </ListItem>
                            ))}
                          </List>
                        </Paper>
                      )}
                    </Stack>
                  )}
                </Box>
              )}

              {/* TAB 2: LEARNING ROADMAP */}
              {activeTab === 2 && (
                <Box id="learning-roadmap-tab-content">
                  <LearningRoadmapView
                    targetRole={targetRole}
                    setTargetRole={setTargetRole}
                    targetLocation={targetLocation}
                    setTargetLocation={setTargetLocation}
                    onGenerateRoadmap={() => handleGenerateRoadmap(false)}
                    roadmapStatus={roadmapStatus}
                    roadmapError={roadmapError}
                    roadmapResult={roadmapResult}
                    disabled={!uploadedResume}
                  />
                </Box>
              )}
            </Box>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default SkillGapPage;
