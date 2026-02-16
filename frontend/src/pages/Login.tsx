import { useState } from 'react';
import { useNavigate, Link as RouterLink, useLocation } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Container,
  Paper,
  TextField,
  Typography,
  CircularProgress,
} from '@mui/material';
import Turnstile from 'react-turnstile';
import { authApi } from '../services/api';

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || '';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [captchaToken, setCaptchaToken] = useState('');
  const [captchaKey, setCaptchaKey] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendingEmail, setResendingEmail] = useState(false);
  const [resendSuccess, setResendSuccess] = useState('');

  const needVerification = location.state?.needVerification;

  const handleResendVerification = async () => {
    setResendingEmail(true);
    setResendSuccess('');
    try {
      const res = await authApi.resendVerification();
      setResendSuccess(res.message);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resend verification email');
    } finally {
      setResendingEmail(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (TURNSTILE_SITE_KEY && !captchaToken) {
      setError('Please complete the captcha');
      return;
    }

    setLoading(true);

    try {
      const result = await authApi.login(email, password, captchaToken || 'no-captcha');
      localStorage.setItem('access_token', result.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
      setCaptchaToken('');
      setCaptchaKey((k) => k + 1);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom textAlign="center">
          Login
        </Typography>

        {needVerification && (
          <Alert severity="warning" sx={{ mb: 2 }}
            action={
              <Button
                color="inherit"
                size="small"
                disabled={resendingEmail}
                onClick={handleResendVerification}
              >
                {resendingEmail ? 'Sending...' : 'Resend'}
              </Button>
            }
          >
            Your email address needs to be verified. Please check your inbox for the verification link.
          </Alert>
        )}

        {resendSuccess && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setResendSuccess('')}>
            {resendSuccess}
          </Alert>
        )}

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
            autoComplete="current-password"
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
            {loading ? <CircularProgress size={24} /> : 'Login'}
          </Button>

          <Typography variant="body2" align="center" sx={{ mt: 2 }}>
            Don't have an account?{' '}
            <RouterLink to="/register">Register</RouterLink>
          </Typography>

          <Typography variant="body2" align="center" sx={{ mt: 1 }}>
            <RouterLink to="/forgot-password">Forgot password?</RouterLink>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
}
