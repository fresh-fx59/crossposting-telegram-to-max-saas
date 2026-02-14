import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  Container,
  Fab,
  IconButton,
  LinearProgress,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Link as MuiLink,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { connectionsApi, type Connection, type TelegramConnection } from '../services/api';

export default function Dashboard() {
  const navigate = useNavigate();
  const [connections, setConnections] = useState<Connection[]>([]);
  const [telegramConnections, setTelegramConnections] = useState<TelegramConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [user, setUser] = useState<any>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newTelegramUsername, setNewTelegramUsername] = useState('');
  const [newBotToken, setNewBotToken] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [conns, tgConns, userData] = await Promise.all([
        connectionsApi.listConnections(),
        connectionsApi.listTelegramConnections(),
        connectionsApi.getUser?.() || (await fetch('/auth/me').then(r => r.json())),
      ]);
      setConnections(conns);
      setTelegramConnections(tgConns);
      setUser(userData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load connections');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTelegram = async () => {
    try {
      await connectionsApi.createTelegramConnection(newTelegramUsername, newBotToken);
      setCreateDialogOpen(false);
      setNewTelegramUsername('');
      setNewBotToken('');
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create connection');
    }
  };

  const handleCreateConnection = async (tgConnId: number) => {
    if (!user?.max_chat_id) {
      setError('Please set your Max credentials in Settings first');
      navigate('/settings');
      return;
    }

    try {
      await connectionsApi.createConnection(tgConnId, user.max_chat_id, 'New Connection');
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create connection');
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {!user?.is_email_verified && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Please verify your email address to create connections.
        </Alert>
      )}

      {loading ? (
        <LinearProgress />
      ) : connections.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" gutterBottom color="text.secondary">
            No connections yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Add a Telegram channel and create your first connection
          </Typography>
          {telegramConnections.length === 0 ? (
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateDialogOpen(true)}>
              Add Telegram Channel
            </Button>
          ) : (
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => {}}>
              Create Connection
            </Button>
          )}
        </Box>
      ) : (
        <Box sx={{ display: 'grid', gap: 2 }}>
          {connections.map((conn) => (
            <Card key={conn.id}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Typography variant="h6" component="h2">
                      {conn.name || `Connection ${conn.id}`}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      @{conn.telegram_channel_username || conn.telegram_channel_id} → {conn.max_chat_id}
                    </Typography>
                    <Chip
                      icon={conn.is_active ? <CheckCircleIcon /> : <ErrorIcon />}
                      label={conn.is_active ? 'Active' : 'Inactive'}
                      color={conn.is_active ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                  <CardActions sx={{ p: 0 }}>
                    <MuiLink component="button" onClick={() => navigate(`/connections/${conn.id}`)}>
                      View Details
                    </MuiLink>
                  </CardActions>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}

      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => {
          if (telegramConnections.length === 0) {
            setCreateDialogOpen(true);
          }
        }}
      >
        <AddIcon />
      </Fab>

      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Telegram Channel</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            label="Channel Username"
            placeholder="@yourchannel"
            fullWidth
            value={newTelegramUsername}
            onChange={(e) => setNewTelegramUsername(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            label="Bot Token"
            placeholder="From @BotFather"
            fullWidth
            value={newBotToken}
            onChange={(e) => setNewBotToken(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateTelegram} variant="contained">Add</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}