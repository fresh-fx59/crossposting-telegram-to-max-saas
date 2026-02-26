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
import { useLanguage } from '../i18n/LanguageContext';

export default function Account() {
  const navigate = useNavigate();
  const { t } = useLanguage();
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
      setError(t.account.failedToLoad);
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
        {t.account.title}
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t.account.info}
          </Typography>
          <Typography>{t.account.email}: {user?.email}</Typography>
          <Typography>
            {t.account.emailVerified}: {user?.is_email_verified ? t.account.yes : t.account.no}
          </Typography>
          <Typography>{t.account.connectionsLimit}: {user?.connections_limit}</Typography>
          <Typography>{t.account.dailyPostsLimit}: {user?.daily_posts_limit}</Typography>
          <Typography>
            {t.account.signedUp}: {user?.created_at ? new Date(user.created_at).toLocaleString() : ''}
          </Typography>

          <Box sx={{ mt: 3 }}>
            <Button variant="outlined" color="error" onClick={handleLogout}>
              {t.account.logout}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
}
