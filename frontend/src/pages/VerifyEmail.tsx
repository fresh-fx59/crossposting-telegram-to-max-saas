import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Alert, Container, Typography, LinearProgress } from '@mui/material';
import { authApi } from '../services/api';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const verifyToken = async () => {
      const token = searchParams.get('token');
      
      if (!token) {
        setError('No verification token provided');
        setLoading(false);
        return;
      }

      try {
        await authApi.verifyEmail(token);
        setSuccess(true);
        setError('');
        
        // Wait a moment before redirecting to show success message
        setTimeout(() => {
          navigate('/dashboard');
        }, 3000);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Email verification failed');
      } finally {
        setLoading(false);
      }
    };

    verifyToken();
  }, [searchParams, navigate]);

  return (
    <Container maxWidth="sm" sx={{ mt: 8, p: 4 }}>
      <Typography variant="h4" component="h1" align="center" gutterBottom>
        Email Verification
      </Typography>

      {loading && (
        <LinearProgress sx={{ mb: 2 }} />
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Email verified successfully! Redirecting to dashboard...
        </Alert>
      )}

      {!loading && !success && !error && (
        <Typography variant="body1" align="center">
          Verifying your email address...
        </Typography>
      )}
    </Container>
  );
}