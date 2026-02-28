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
import { useLanguage } from '../i18n/LanguageContext';
import { setStoredValue } from '../services/storage';

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || '';

export default function Register() {
  const navigate = useNavigate();
  const { t } = useLanguage();
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
      setError(t.register.errors.passwordsMismatch);
      return;
    }

    if (password.length < 8) {
      setError(t.register.errors.passwordTooShort);
      return;
    }

    if (TURNSTILE_SITE_KEY && !captchaToken) {
      setError(t.register.errors.captchaRequired);
      return;
    }

    setLoading(true);

    try {
      const result = await authApi.register(email, password, captchaToken || 'no-captcha');
      setStoredValue('access_token', result.access_token);
      setSuccess(true);
      setTimeout(() => navigate('/dashboard'), 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || t.register.errors.registrationFailed);
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
            {t.register.successMessage.replace('{email}', email)}
          </Alert>
          <Typography>{t.register.redirecting}</Typography>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom textAlign="center">
          {t.register.title}
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            label={t.register.email}
            type="email"
            fullWidth
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            margin="normal"
            required
            autoComplete="email"
          />
          <TextField
            label={t.register.password}
            type="password"
            fullWidth
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
            required
            autoComplete="new-password"
            helperText={t.register.passwordHelper}
          />
          <TextField
            label={t.register.confirmPassword}
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
            {loading ? <CircularProgress size={24} /> : t.register.submit}
          </Button>

          <Typography variant="body2" align="center" sx={{ mt: 2 }}>
            {t.register.hasAccount}{' '}
            <RouterLink to="/login">{t.register.loginLink}</RouterLink>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
}
