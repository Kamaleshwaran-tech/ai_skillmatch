import React, { useState } from 'react';
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Card,
  CardContent,
  Stack,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import SearchIcon from '@mui/icons-material/Search';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  CartesianGrid,
} from 'recharts';
import { fetchMarketDemand } from '../services/skillGapService';
import SampleDataBanner from '../components/SampleDataBanner';

export const MarketDemandPage = () => {
  const [roleInput, setRoleInput] = useState('');
  const [locationInput, setLocationInput] = useState('');
  const [appliedFilters, setAppliedFilters] = useState({ role: '', location: '' });

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['marketDemand', appliedFilters.role, appliedFilters.location],
    queryFn: () =>
      fetchMarketDemand({
        role: appliedFilters.role,
        location: appliedFilters.location,
        limit: 30,
      }),
    staleTime: 1000 * 60 * 5,
  });

  const handleSearch = (e) => {
    e.preventDefault();
    setAppliedFilters({ role: roleInput.trim(), location: locationInput.trim() });
  };

  const getPriorityColor = (pct) => {
    if (pct >= 70) return '#ef4444'; // Red for High
    if (pct >= 40) return '#f59e0b'; // Amber for Medium
    return '#3b82f6'; // Blue for Low
  };

  const chartData = (data?.top_skills || []).slice(0, 10).map((s) => ({
    name: s.skill_name,
    demandPercentage: s.demand_percentage,
    listingsCount: s.matching_listings_count,
    totalAnalyzed: s.total_listings_analyzed,
  }));

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 1 }}>
          <TrendingUpIcon color="primary" sx={{ fontSize: 36 }} />
          <Typography variant="h4" sx={{ fontWeight: 800 }}>
            Market Skill Demand Analytics
          </Typography>
        </Stack>
        <Typography variant="body1" color="text.secondary">
          Real-time telemetry and technical demand analysis aggregated across live and sample job postings.
        </Typography>
      </Box>

      {/* SAMPLE DATA BANNER */}
      <SampleDataBanner
        isSampleData={data?.is_sample_data}
        message={data?.banner_message}
      />

      {/* Search Filters Bar */}
      <Paper elevation={1} sx={{ p: 3, mb: 4, borderRadius: 2 }}>
        <Box component="form" onSubmit={handleSearch}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={5}>
              <TextField
                id="role-filter-input"
                label="Target Role or Tech Stack"
                placeholder="e.g. Developer, Python, Frontend"
                fullWidth
                size="small"
                value={roleInput}
                onChange={(e) => setRoleInput(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                id="location-filter-input"
                label="Location or Remote"
                placeholder="e.g. San Francisco, CA or Remote"
                fullWidth
                size="small"
                value={locationInput}
                onChange={(e) => setLocationInput(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <Button
                id="search-demand-button"
                type="submit"
                variant="contained"
                fullWidth
                startIcon={isFetching ? <CircularProgress size={18} color="inherit" /> : <SearchIcon />}
                disabled={isFetching}
                sx={{ height: 40 }}
              >
                Analyze Market
              </Button>
            </Grid>
          </Grid>
        </Box>
      </Paper>

      {/* LOADING STATE */}
      {isLoading && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <CircularProgress size={40} />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Querying market listings and calculating skill frequencies...
          </Typography>
        </Box>
      )}

      {/* ERROR STATE */}
      {isError && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error?.response?.data?.detail || error?.message || 'Failed to fetch market demand.'}
        </Alert>
      )}

      {/* EMPTY / INSUFFICIENT DATA STATE */}
      {data && data.status === 'insufficient_data' && (
        <Alert severity="info" sx={{ mb: 4 }}>
          {data.message || 'No job listings found for the specified filters.'}
        </Alert>
      )}

      {/* DATA VISUALIZATION & TABLE */}
      {data && data.status === 'sufficient_data' && (
        <Grid container spacing={4}>
          {/* Metrics Card */}
          <Grid item xs={12}>
            <Card variant="outlined" sx={{ bgcolor: '#f0fdf4', borderColor: '#bbf7d0', p: 1 }}>
              <CardContent>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={3} alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="overline" color="text.secondary">
                      Dataset Denominator
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 800, color: '#166534' }}>
                      {data.total_unique_listings_analyzed} Unique Listings Analyzed
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      All percentages calculated as: (listings with skill / {data.total_unique_listings_analyzed}) × 100
                    </Typography>
                  </Box>
                  <Chip
                    icon={<AnalyticsIcon />}
                    label={`${data.top_skills.length} Technical Skills Extracted`}
                    color="success"
                    variant="outlined"
                  />
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {/* Bar Chart: Top 10 Skills */}
          <Grid item xs={12} md={7}>
            <Paper elevation={2} sx={{ p: 3, borderRadius: 2, height: '100%' }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                Top 10 In-Demand Skills
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                Percentage of analyzed postings requiring each skill (Denominator = {data.total_unique_listings_analyzed})
              </Typography>
              <Box sx={{ width: '100%', height: 360 }}>
                <ResponsiveContainer>
                  <BarChart data={chartData} layout="vertical" margin={{ left: 30, right: 30, top: 10, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" domain={[0, 100]} unit="%" />
                    <YAxis dataKey="name" type="category" width={110} tick={{ fontSize: 13 }} />
                    <Tooltip
                      formatter={(val, name, item) => [
                        `${val}% (${item.payload.listingsCount} of ${item.payload.totalAnalyzed} listings)`,
                        'Demand',
                      ]}
                    />
                    <Bar dataKey="demandPercentage" radius={[0, 4, 4, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getPriorityColor(entry.demandPercentage)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </Paper>
          </Grid>

          {/* Table: Skill Demographics & Denominators */}
          <Grid item xs={12} md={5}>
            <Paper elevation={2} sx={{ p: 3, borderRadius: 2, height: '100%' }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                Skill Frequency Breakdown
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                Showing exact count and denominator
              </Typography>
              <TableContainer sx={{ maxHeight: 360 }}>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Skill</strong></TableCell>
                      <TableCell align="center"><strong>Ratio</strong></TableCell>
                      <TableCell align="right"><strong>Demand %</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.top_skills.map((s) => (
                      <TableRow key={s.skill_name} hover>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {s.skill_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {s.category}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={`${s.matching_listings_count} / ${s.total_listings_analyzed}`}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography
                            variant="body2"
                            sx={{ fontWeight: 700, color: getPriorityColor(s.demand_percentage) }}
                          >
                            {s.demand_percentage.toFixed(1)}%
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Container>
  );
};

export default MarketDemandPage;
