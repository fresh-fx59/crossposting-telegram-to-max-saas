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
import { useLanguage } from '../i18n/LanguageContext';

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || '';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useLanguage();
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
      setError(err.response?.data?.detail || t.login.errors.resendFailed);
    } finally {
      setResendingEmail(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (TURNSTILE_SITE_KEY && !captchaToken) {
      setError(t.login.errors.captchaRequired);
      return;
    }

    setLoading(true);

    try {
      const result = await authApi.login(email, password, captchaToken || 'no-captcha');
      localStorage.setItem('access_token', result.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || t.login.errors.loginFailed);
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
          {t.login.title}
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
                {resendingEmail ? t.login.sending : t.login.resend}
              </Button>
            }
          >
            {t.login.verificationNeeded}
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
            label={t.login.email}
            type="email"
            fullWidth
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            margin="normal"
            required
            autoComplete="email"
          />
          <TextField
            label={t.login.password}
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
            {loading ? <CircularProgress size={24} /> : t.login.submit}
          </Button>

          <Typography variant="body2" align="center" sx={{ mt: 2 }}>
            {t.login.noAccount}{' '}
            <RouterLink to="/register">{t.login.registerLink}</RouterLink>
          </Typography>

          <Typography variant="body2" align="center" sx={{ mt: 1 }}>
            <RouterLink to="/forgot-password">{t.login.forgotPassword}</RouterLink>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
}
