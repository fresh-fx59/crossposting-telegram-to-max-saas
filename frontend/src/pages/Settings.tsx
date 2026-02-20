import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Container,
  Card,
  CardContent,
  Typography,
  CircularProgress,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { authApi, type User } from '../services/api';

export default function Account() {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      setLoading(true);
      const userData = await authApi.getMe();
      setUser(userData);
    } catch {
      setError('Failed to load user data');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
      navigate('/login');
    } catch {
      // Token already removed by logout
      navigate('/login');
    }
  };

  if (loading) {
    return (
      <Container maxWidth="sm" sx={{ py: 4 }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Account
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Account Information
          </Typography>
          <Typography>Email: {user?.email}</Typography>
          <Typography>
            Email verified: {user?.is_email_verified ? 'Yes' : 'No'}
          </Typography>
          <Typography>Connections limit: {user?.connections_limit}</Typography>
          <Typography>Daily posts limit: {user?.daily_posts_limit}</Typography>
          <Typography>
            Signed up: {user?.created_at ? new Date(user.created_at).toLocaleString() : ''}
          </Typography>

          <Box sx={{ mt: 3 }}>
            <Button variant="outlined" color="error" onClick={handleLogout}>
              Logout
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
}
