import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Chip,
  Stack,
  Button,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import BusinessIcon from '@mui/icons-material/Business';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

export const RecommendedJobCard = ({ job }) => {
  const isScorable = job.is_scorable !== false && job.match_percentage !== null && job.match_percentage !== undefined;
  const matchPct = isScorable ? job.match_percentage : null;

  // Determine badge and bar color based on match percentage
  let badgeColor = '#16a34a'; // green for high
  let badgeBg = '#dcfce7';
  let progressColor = 'success';
  if (!isScorable) {
    badgeColor = '#64748b'; // slate/gray for unscored
    badgeBg = '#f1f5f9';
    progressColor = 'inherit';
  } else if (matchPct < 40) {
    badgeColor = '#2563eb'; // blue for low
    badgeBg = '#dbeafe';
    progressColor = 'info';
  } else if (matchPct < 70) {
    badgeColor = '#d97706'; // amber for medium
    badgeBg = '#fef3c7';
    progressColor = 'warning';
  }

  // Format posted date
  const formattedDate = job.posted_date
    ? new Date(job.posted_date).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : null;

  return (
    <Card
      variant="outlined"
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 2.5,
        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 3,
        },
        borderColor: '#e2e8f0',
      }}
    >
      <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
        {/* Top Header: Title & Prominent Match Badge */}
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1.5} sx={{ mb: 1.5 }}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" component="h3" sx={{ fontWeight: 700, fontSize: '1.1rem', lineHeight: 1.3 }}>
              {job.title}
            </Typography>
            <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap" sx={{ mt: 0.5, color: 'text.secondary' }}>
              <Stack direction="row" spacing={0.5} alignItems="center">
                <BusinessIcon fontSize="inherit" sx={{ fontSize: 16 }} />
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {job.company}
                </Typography>
              </Stack>
              {job.location && (
                <Stack direction="row" spacing={0.5} alignItems="center">
                  <LocationOnIcon fontSize="inherit" sx={{ fontSize: 16 }} />
                  <Typography variant="body2">{job.location}</Typography>
                </Stack>
              )}
            </Stack>
          </Box>

          {/* Prominent Match Badge */}
          <Tooltip
            title={
              isScorable
                ? `Resume matches ${matchPct}% of detected job requirements`
                : 'Job listing description had insufficient skill details to calculate a match score'
            }
          >
            <Box
              sx={{
                bgcolor: badgeBg,
                color: badgeColor,
                px: 1.5,
                py: 0.75,
                borderRadius: 2,
                textAlign: 'center',
                minWidth: 70,
                flexShrink: 0,
                border: `1px solid ${badgeColor}33`,
              }}
            >
              <Typography variant="h6" sx={{ fontWeight: 800, fontSize: '1.05rem', lineHeight: 1 }}>
                {isScorable ? `${matchPct}%` : 'N/A'}
              </Typography>
              <Typography variant="caption" sx={{ fontWeight: 700, fontSize: '0.65rem', textTransform: 'uppercase' }}>
                {isScorable ? 'Match' : 'Unscored'}
              </Typography>
            </Box>
          </Tooltip>
        </Stack>

        {/* Visual Match Progress Bar */}
        <Box sx={{ mb: 2 }}>
          <LinearProgress
            variant="determinate"
            value={isScorable ? matchPct : 0}
            color={progressColor}
            sx={{ height: 6, borderRadius: 3, bgcolor: '#f1f5f9' }}
          />
        </Box>

        {/* Salary & Date Row */}
        {(job.salary_range || formattedDate) && (
          <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap" sx={{ mb: 2, fontSize: '0.85rem', color: 'text.secondary' }}>
            {job.salary_range && (
              <Stack direction="row" spacing={0.5} alignItems="center">
                <MonetizationOnIcon fontSize="inherit" sx={{ fontSize: 16, color: '#16a34a' }} />
                <Typography variant="caption" sx={{ fontWeight: 600, color: '#15803d' }}>
                  {job.salary_range}
                </Typography>
              </Stack>
            )}
            {formattedDate && (
              <Stack direction="row" spacing={0.5} alignItems="center">
                <CalendarTodayIcon fontSize="inherit" sx={{ fontSize: 15 }} />
                <Typography variant="caption">{formattedDate}</Typography>
              </Stack>
            )}
          </Stack>
        )}

        {/* Description Snippet */}
        {job.description_snippet && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              mb: 2,
              lineHeight: 1.5,
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {job.description_snippet}
          </Typography>
        )}

        {/* Matched Skills Chips (Highlighted/Green) */}
        <Box sx={{ mb: 1.5 }}>
          <Stack direction="row" spacing={0.5} alignItems="center" sx={{ mb: 0.75 }}>
            <CheckCircleOutlineIcon sx={{ fontSize: 16, color: '#16a34a' }} />
            <Typography variant="caption" sx={{ fontWeight: 700, color: '#15803d', textTransform: 'uppercase' }}>
              Matched Skills ({job.matched_skills?.length || 0})
            </Typography>
          </Stack>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
            {job.matched_skills && job.matched_skills.length > 0 ? (
              job.matched_skills.map((skill, idx) => (
                <Chip
                  key={`match-${idx}`}
                  label={skill}
                  size="small"
                  sx={{
                    bgcolor: '#dcfce7',
                    color: '#15803d',
                    fontWeight: 600,
                    fontSize: '0.75rem',
                    border: '1px solid #bbf7d0',
                  }}
                />
              ))
            ) : (
              <Typography variant="caption" color="text.secondary">
                No direct skill matches detected.
              </Typography>
            )}
          </Box>
        </Box>

        {/* Missing Skills Chips (Muted/Gray) */}
        {job.missing_skills && job.missing_skills.length > 0 && (
          <Box>
            <Stack direction="row" spacing={0.5} alignItems="center" sx={{ mb: 0.75 }}>
              <ErrorOutlineIcon sx={{ fontSize: 16, color: '#94a3b8' }} />
              <Typography variant="caption" sx={{ fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                Skills to Acquire ({job.missing_skills.length})
              </Typography>
            </Stack>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
              {job.missing_skills.map((skill, idx) => (
                <Chip
                  key={`miss-${idx}`}
                  label={skill}
                  size="small"
                  variant="outlined"
                  sx={{
                    color: '#64748b',
                    borderColor: '#cbd5e1',
                    bgcolor: '#f8fafc',
                    fontSize: '0.75rem',
                  }}
                />
              ))}
            </Box>
          </Box>
        )}
      </CardContent>

      {/* Card Actions: Apply Button */}
      <CardActions sx={{ px: 2.5, pb: 2.5, pt: 0 }}>
        <Button
          component="a"
          href={job.apply_url || '#'}
          target="_blank"
          rel="noopener noreferrer"
          variant="contained"
          fullWidth
          size="medium"
          endIcon={<OpenInNewIcon />}
          disabled={!job.apply_url}
          sx={{
            fontWeight: 700,
            textTransform: 'none',
            borderRadius: 1.5,
          }}
          className="apply-job-link"
        >
          Apply on Adzuna
        </Button>
      </CardActions>
    </Card>
  );
};

export default RecommendedJobCard;
