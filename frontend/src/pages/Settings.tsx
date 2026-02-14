import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Container,
  Card,
  CardContent,
  TextField,
  Typography,
  CircularProgress,
} from '@mui/material';
import { authApi, usersApi, type User } from '../services/api';

export default function Settings() {
  const [user, setUser] = useState<User | null>(null);
  const [maxToken, setMaxToken] = useState('');
  const [maxChatId, setMaxChatId] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error'>('success');

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      setLoading(true);
      const userData = await authApi.getMe();
      setUser(userData);
      setMaxChatId(userData.max_chat_id?.toString() || '');
    } catch (err) {
      setMessage('Failed to load user data');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    try {
      await usersApi.updateMe(maxToken || null, maxChatId ? Number(maxChatId) : null);
      setMessage('Settings saved successfully');
      setMessageType('success');
      await loadUser();
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Failed to save settings');
      setMessageType('error');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setMessage('');
    try {
      await usersApi.testMax();
      setMessage('Test message sent successfully!');
      setMessageType('success');
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Failed to send test message');
      setMessageType('error');
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>

      {message && (
        <Alert severity={messageType} sx={{ mb: 2 }} onClose={() => setMessage('')}>
          {message}
        </Alert>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            MAX Credentials
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Configure your Max bot token and target chat ID for forwarding messages.
          </Typography>

          {!user?.is_email_verified && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Please verify your email address to save settings.
            </Alert>
          )}

          <TextField
            label="Max Bot Token"
            placeholder="Enter your Max bot token"
            fullWidth
            margin="normal"
            value={maxToken}
            onChange={(e) => setMaxToken(e.target.value)}
            disabled={!user?.is_email_verified}
          />

          <TextField
            label="Max Chat ID"
            placeholder="Enter target chat ID"
            fullWidth
            margin="normal"
            value={maxChatId}
            onChange={(e) => setMaxChatId(e.target.value)}
            disabled={!user?.is_email_verified}
          />

          <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              onClick={handleSave}
              disabled={saving || !user?.is_email_verified}
            >
              {saving ? <CircularProgress size={20} /> : 'Save'}
            </Button>
            <Button
              variant="outlined"
              onClick={handleTest}
              disabled={testing || !user?.is_email_verified || !user?.max_token_set}
            >
              {testing ? <CircularProgress size={20} /> : 'Test Connection'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Account Information
          </Typography>
          <Typography>Email: {user?.email}</Typography>
          <Typography>Max Token: {user?.max_token_set ? 'Configured' : 'Not set'}</Typography>
          <Typography>Max Chat ID: {user?.max_chat_id || 'Not set'}</Typography>
          <Typography>Signed up: {user?.created_at ? new Date(user.created_at).toLocaleString() : ''}</Typography>
        </CardContent>
      </Card>
    </Container>
  );
}