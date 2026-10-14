import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, Chip } from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import LoginIcon from '@mui/icons-material/Login';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import RouteIcon from '@mui/icons-material/Route';
import { Link, useNavigate } from 'react-router-dom';
import { APP_NAME, ROUTES } from '../utils/constants';
import { useAuth } from '../hooks/useAuth';

export const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <AppBar position="static" color="default" elevation={1}>
      <Toolbar>
        <AutoAwesomeIcon color="primary" sx={{ mr: 1.5 }} />
        <Typography
          variant="h6"
          component={Link}
          to="/"
          sx={{
            fontWeight: 700,
            letterSpacing: '-0.5px',
            color: 'inherit',
            textDecoration: 'none',
          }}
        >
          {APP_NAME}
        </Typography>
        <Chip
          label="v0.1.0"
          size="small"
          color="primary"
          variant="outlined"
          sx={{ ml: 1.5, height: 20, fontSize: '0.75rem' }}
        />
        <Box sx={{ flexGrow: 1 }} />
        <Button color="inherit" component={Link} to="/">
          Home
        </Button>
        <Button
          color="inherit"
          component={Link}
          to="/market-demand"
          startIcon={<TrendingUpIcon />}
        >
          Market Demand
        </Button>
        <Button
          color="inherit"
          component={Link}
          to="/skill-gap"
          startIcon={<CompareArrowsIcon />}
        >
          Skill Gap Analysis
        </Button>
        <Button
          color="inherit"
          component={Link}
          to="/roadmap"
          startIcon={<RouteIcon />}
          id="nav-learning-roadmap"
        >
          Learning Roadmap
        </Button>

        {isAuthenticated && user ? (
          <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}>
            <Button
              color="primary"
              variant="outlined"
              component={Link}
              to={ROUTES.AUTH}
              startIcon={<AccountCircleIcon />}
              sx={{ mr: 1.5 }}
            >
              {user.full_name || user.email}
            </Button>
            <Button
              color="inherit"
              size="small"
              onClick={() => {
                logout();
                navigate('/');
              }}
            >
              Sign Out
            </Button>
          </Box>
        ) : (
          <Button
            variant="contained"
            color="primary"
            component={Link}
            to={ROUTES.AUTH}
            startIcon={<LoginIcon />}
            sx={{ ml: 2, textTransform: 'none' }}
          >
            Sign In / Register
          </Button>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
