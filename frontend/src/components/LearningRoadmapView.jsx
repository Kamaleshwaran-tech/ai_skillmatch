import React from 'react';
import {
  Box,
  Paper,
  Grid,
  TextField,
  Button,
  CircularProgress,
  LinearProgress,
  Alert,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import RouteIcon from '@mui/icons-material/Route';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import BuildCircleOutlinedIcon from '@mui/icons-material/BuildCircleOutlined';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

export const LearningRoadmapView = ({
  targetRole,
  setTargetRole,
  targetLocation,
  setTargetLocation,
  onGenerateRoadmap,
  roadmapStatus,
  roadmapError,
  roadmapResult,
  disabled = false,
}) => {
  const isGenerating = roadmapStatus === 'loading';

  const getPriorityChip = (priority) => {
    let color = 'default';
    if (priority === 'High') color = 'error';
    else if (priority === 'Medium') color = 'warning';
    else if (priority === 'Low') color = 'info';

    return (
      <Chip
        label={`Priority: ${priority}`}
        size="small"
        color={color}
        sx={{ fontWeight: 600 }}
      />
    );
  };

  const getDemandColor = (pct) => {
    if (pct >= 70) return '#ef4444'; // Red for High
    if (pct >= 40) return '#f59e0b'; // Amber for Medium
    return '#3b82f6'; // Blue for Low
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onGenerateRoadmap) {
      onGenerateRoadmap();
    }
  };

  return (
    <Box id="learning-roadmap-view">
      {/* Role & Location Input Bar (reusing Market Demand search pattern) */}
      <Paper elevation={1} sx={{ p: 2.5, mb: 3, borderRadius: 2 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={5}>
              <TextField
                id="roadmap-role-input"
                label="Target Role or Tech Stack"
                placeholder="e.g. Developer, Python, Frontend"
                fullWidth
                size="small"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                id="roadmap-location-input"
                label="Location or Remote (Optional)"
                placeholder="e.g. San Francisco, CA or Remote"
                fullWidth
                size="small"
                value={targetLocation}
                onChange={(e) => setTargetLocation(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <Button
                id="generate-roadmap-button"
                type="submit"
                variant="contained"
                color="primary"
                fullWidth
                disabled={disabled || isGenerating || !targetRole?.trim()}
                startIcon={
                  isGenerating ? (
                    <CircularProgress size={18} color="inherit" />
                  ) : (
                    <PlayArrowIcon />
                  )
                }
                sx={{ height: 40 }}
              >
                {isGenerating ? 'Generating...' : 'Generate Roadmap'}
              </Button>
            </Grid>
          </Grid>
        </Box>
      </Paper>

      {/* Rich Contextual Loading State while Roadmap & LLM explanations generate */}
      {isGenerating && (
        <Paper
          elevation={2}
          sx={{ p: 5, textAlign: 'center', borderRadius: 2, mb: 3 }}
          id="roadmap-loading-state"
        >
          <CircularProgress size={44} sx={{ mb: 2 }} />
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
            Building Your Personalized Learning Roadmap for "{targetRole}"
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ maxWidth: 560, mx: 'auto', mb: 3 }}
          >
            Step 1: Evaluating resume against real market demand • Step 2: Ordering missing skills by highest market opportunity • Step 3: Generating AI explanations & resource guidance per skill...
          </Typography>
          <Box sx={{ maxWidth: 420, mx: 'auto' }}>
            <LinearProgress sx={{ height: 8, borderRadius: 4 }} />
          </Box>
        </Paper>
      )}

      {/* Error State */}
      {roadmapStatus === 'error' && (
        <Alert severity="error" sx={{ mb: 3 }} id="roadmap-error-alert">
          {roadmapError || 'Failed to generate learning roadmap.'}
        </Alert>
      )}

      {/* Initial Idle Prompt */}
      {!roadmapResult && !isGenerating && roadmapStatus !== 'error' && (
        <Paper
          variant="outlined"
          sx={{ p: 5, textAlign: 'center', borderRadius: 2.5, bgcolor: '#ffffff' }}
          id="roadmap-idle-prompt"
        >
          <RouteIcon sx={{ fontSize: 48, color: '#94a3b8', mb: 1.5 }} />
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
            Ready to Generate Your Learning Roadmap
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ maxWidth: 460, mx: 'auto', mb: 2.5 }}
          >
            Enter a target role above and click <strong>Generate Roadmap</strong> to order your missing skills by real market demand and receive structured learning guidance.
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={onGenerateRoadmap}
            disabled={disabled || !targetRole?.trim()}
            startIcon={<PlayArrowIcon />}
          >
            Generate Roadmap for "{targetRole || 'Developer'}"
          </Button>
        </Paper>
      )}

      {/* Roadmap Results */}
      {roadmapResult && !isGenerating && (
        <Stack spacing={3} id="roadmap-results-panel">
          {/* Top Match Scorecard (Same visual style as Skill Gap Match %) */}
          <Card variant="outlined" sx={{ bgcolor: '#ffffff', borderRadius: 2 }} id="roadmap-match-scorecard">
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                Target Role: <strong>{roadmapResult.target_role}</strong>
                {roadmapResult.target_location ? ` (${roadmapResult.target_location})` : ''}
              </Typography>
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                justifyContent="space-between"
                alignItems={{ xs: 'flex-start', sm: 'center' }}
                spacing={1}
                sx={{ mb: 1 }}
              >
                <Typography variant="h5" sx={{ fontWeight: 800 }} id="roadmap-overall-match-pct">
                  Competency Match: {roadmapResult.overall_match_percentage}%
                </Typography>
                <Chip
                  label={`${roadmapResult.total_listings_analyzed} Unique Postings Analyzed`}
                  color="primary"
                  variant="outlined"
                />
              </Stack>
              <LinearProgress
                variant="determinate"
                value={roadmapResult.overall_match_percentage}
                sx={{ height: 10, borderRadius: 5, mb: 2 }}
              />

              {/* Matched Skills Shown Briefly as Chips */}
              <Box
                sx={{ pt: 1.5, borderTop: '1px solid #f1f5f9' }}
                id="roadmap-matched-skills-section"
              >
                <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                  <CheckCircleIcon color="success" fontSize="small" />
                  <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                    Already Matched Skills ({roadmapResult.matched_skills?.length || 0})
                  </Typography>
                </Stack>
                {!roadmapResult.matched_skills || roadmapResult.matched_skills.length === 0 ? (
                  <Typography variant="caption" color="text.secondary">
                    No demanded skills currently matched for this role yet.
                  </Typography>
                ) : (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                    {roadmapResult.matched_skills.map((item, idx) => (
                      <Chip
                        key={idx}
                        label={`${item.skill} (${item.demand_percentage}%)`}
                        size="small"
                        color="success"
                        variant="outlined"
                        sx={{ fontWeight: 600 }}
                        data-testid="roadmap-matched-skill-chip"
                      />
                    ))}
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>

          {/* Empty State if 0 Listings Analyzed vs 0 Missing Skills (100% Matched) */}
          {roadmapResult.total_listings_analyzed === 0 ? (
            <Alert severity="info" id="roadmap-no-listings-alert">
              No job listings were found matching "{roadmapResult.target_role}". Try a broader role title such as "Developer" or "Software Engineer".
            </Alert>
          ) : roadmapResult.roadmap_steps.length === 0 ? (
            <Paper
              elevation={1}
              sx={{
                p: 5,
                textAlign: 'center',
                borderRadius: 2.5,
                bgcolor: '#f0fdf4',
                border: '1px solid #bbf7d0',
              }}
              id="roadmap-fully-matched-state"
            >
              <CheckCircleIcon color="success" sx={{ fontSize: 56, mb: 1.5 }} />
              <Typography variant="h6" sx={{ fontWeight: 800, color: '#166534', mb: 1 }}>
                You're Fully Matched for "{roadmapResult.target_role}"!
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 480, mx: 'auto' }}>
                Your resume already covers all in-demand competencies identified across the analyzed job postings. No additional learning steps are required for this role.
              </Typography>
            </Paper>
          ) : (
            /* Ordered Learning Sequence Stepper */
            <Paper elevation={1} sx={{ p: 3, borderRadius: 2 }} id="roadmap-steps-container">
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                justifyContent="space-between"
                alignItems={{ xs: 'flex-start', sm: 'center' }}
                spacing={1}
                sx={{ mb: 1 }}
              >
                <Stack direction="row" spacing={1} alignItems="center">
                  <TrendingUpIcon color="primary" />
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Ordered Learning Roadmap ({roadmapResult.roadmap_steps.length} Steps)
                  </Typography>
                </Stack>
                <Chip
                  label="Ordered by Market Demand % (Highest First)"
                  size="small"
                  color="primary"
                  variant="outlined"
                  sx={{ fontWeight: 600 }}
                />
              </Stack>

              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                {roadmapResult.priority_thresholds?.note ||
                  'Project-defined priority thresholds: High >= 70%, Medium 40-69%, Low < 40%.'}
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                {roadmapResult.resource_disclaimer}
              </Typography>

              <Divider sx={{ mb: 2.5 }} />

              <Stepper orientation="vertical" nonLinear id="roadmap-stepper">
                {roadmapResult.roadmap_steps.map((step) => (
                  <Step key={step.step_number} active expanded>
                    <StepLabel
                      StepIconProps={{
                        sx: {
                          color: getDemandColor(step.demand_percentage),
                          fontWeight: 700,
                        },
                      }}
                    >
                      <Stack
                        direction={{ xs: 'column', sm: 'row' }}
                        spacing={1}
                        alignItems={{ xs: 'flex-start', sm: 'center' }}
                        flexWrap="wrap"
                      >
                        <Typography
                          variant="subtitle1"
                          sx={{ fontWeight: 800 }}
                          data-testid="roadmap-step-skill-name"
                        >
                          Step {step.step_number}: {step.skill}
                        </Typography>

                        {/* Demand % Badge (Same visual color scheme as Market Demand page) */}
                        <Chip
                          label={`Demand: ${step.demand_percentage}% (${step.matching_listings_count}/${step.total_listings_analyzed})`}
                          size="small"
                          variant="outlined"
                          sx={{
                            fontWeight: 700,
                            borderColor: getDemandColor(step.demand_percentage),
                            color: getDemandColor(step.demand_percentage),
                          }}
                          data-testid="roadmap-step-demand-badge"
                          data-demand-pct={step.demand_percentage}
                        />

                        {getPriorityChip(step.priority)}

                        <Chip
                          label={step.status === 'needs_review' ? 'Needs Review' : 'Missing Skill'}
                          size="small"
                          variant="outlined"
                          color={step.status === 'needs_review' ? 'warning' : 'default'}
                        />
                      </Stack>
                    </StepLabel>

                    <StepContent>
                      <Box
                        sx={{
                          p: 2,
                          mt: 1,
                          mb: 2,
                          borderRadius: 2,
                          bgcolor: '#f8fafc',
                          border: '1px solid #e2e8f0',
                        }}
                        data-testid="roadmap-step-card"
                      >
                        {!step.ai_explanation_available ? (
                          <Alert
                            severity="warning"
                            icon={<WarningAmberIcon fontSize="small" />}
                            sx={{ py: 0.5 }}
                            data-testid="ai-explanation-unavailable-alert"
                          >
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {step.explanation || 'AI explanation unavailable'}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              This skill is ranked #{step.step_number} based on real market demand ({step.demand_percentage}% of analyzed listings).
                            </Typography>
                          </Alert>
                        ) : (
                          <Stack spacing={1.5}>
                            <Typography variant="body2" color="text.primary" data-testid="roadmap-step-explanation">
                              {step.explanation}
                            </Typography>

                            {step.resource_suggestions && step.resource_suggestions.length > 0 && (
                              <Box>
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                  sx={{ fontWeight: 700, textTransform: 'uppercase' }}
                                >
                                  Recommended Resource Types:
                                </Typography>
                                <List dense disablePadding sx={{ mt: 0.5 }}>
                                  {step.resource_suggestions.map((resItem, rIdx) => (
                                    <ListItem key={rIdx} disableGutters sx={{ py: 0.25 }}>
                                      <ListItemIcon sx={{ minWidth: 26 }}>
                                        <MenuBookIcon color="primary" sx={{ fontSize: 16 }} />
                                      </ListItemIcon>
                                      <ListItemText
                                        primary={
                                          <Typography variant="body2" color="text.secondary">
                                            {resItem}
                                          </Typography>
                                        }
                                      />
                                    </ListItem>
                                  ))}
                                </List>
                              </Box>
                            )}

                            {step.practice_project_idea && (
                              <Box
                                sx={{
                                  p: 1.25,
                                  borderRadius: 1.5,
                                  bgcolor: '#eff6ff',
                                  border: '1px solid #bfdbfe',
                                }}
                              >
                                <Stack direction="row" spacing={1} alignItems="center">
                                  <BuildCircleOutlinedIcon color="primary" fontSize="small" />
                                  <Typography variant="caption" sx={{ fontWeight: 700, color: '#1e40af' }}>
                                    Practice Project Idea: {step.practice_project_idea}
                                  </Typography>
                                </Stack>
                              </Box>
                            )}
                          </Stack>
                        )}
                      </Box>
                    </StepContent>
                  </Step>
                ))}
              </Stepper>
            </Paper>
          )}
        </Stack>
      )}
    </Box>
  );
};

export default LearningRoadmapView;
