import { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Paper,
  TextField,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import Turnstile from 'react-turnstile';
import { authApi } from '../services/api';

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || '';

export default function Register() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [captchaToken, setCaptchaToken] = useState('');
  const [captchaKey, setCaptchaKey] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (TURNSTILE_SITE_KEY && !captchaToken) {
      setError('Please complete the captcha');
      return;
    }

    setLoading(true);

    try {
      const result = await authApi.register(email, password, captchaToken || 'no-captcha');
      localStorage.setItem('access_token', result.access_token);
      setSuccess(true);
      setTimeout(() => navigate('/dashboard'), 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed');
      setCaptchaToken('');
      setCaptchaKey((k) => k + 1);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <Container maxWidth="sm" sx={{ mt: 8 }}>
        <Paper sx={{ p: 4 }}>
          <Alert severity="success" sx={{ mb: 2 }}>
            Registration successful! Verification email sent to {email}.
          </Alert>
          <Typography>Redirecting to dashboard...</Typography>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom textAlign="center">
          Create Account
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            label="Email"
            type="email"
            fullWidth
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            margin="normal"
            required
            autoComplete="email"
          />
          <TextField
            label="Password"
            type="password"
            fullWidth
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
            required
            autoComplete="new-password"
            helperText="Minimum 8 characters"
          />
          <TextField
            label="Confirm Password"
            type="password"
            fullWidth
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            margin="normal"
            required
            autoComplete="new-password"
          />

          {TURNSTILE_SITE_KEY && (
            <Box sx={{ my: 2, display: 'flex', justifyContent: 'center' }}>
              <Turnstile
                key={captchaKey}
                sitekey={TURNSTILE_SITE_KEY}
                onVerify={(token: string) => setCaptchaToken(token)}
                onExpire={() => setCaptchaToken('')}
              />
            </Box>
          )}

          <Button
            type="submit"
            variant="contained"
            fullWidth
            size="large"
            disabled={loading || (!!TURNSTILE_SITE_KEY && !captchaToken)}
            sx={{ mt: 2 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Register'}
          </Button>

          <Typography variant="body2" align="center" sx={{ mt: 2 }}>
            Already have an account?{' '}
            <RouterLink to="/login">Login</RouterLink>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
}
