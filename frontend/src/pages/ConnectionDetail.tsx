import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Card,
  Chip,
  Container,
  IconButton,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Pagination,
  Drawer,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  ArrowBack as ArrowBackIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { connectionsApi, type ConnectionDetail } from '../services/api';

export default function ConnectionDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [connection, setConnection] = useState<ConnectionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);

  useEffect(() => {
    loadConnection();
  }, [id, page]);

  const loadConnection = async () => {
    try {
      setLoading(true);
      const conn = await connectionsApi.getConnection(Number(id), page);
      setConnection(conn);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load connection');
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    if (!connection) return;
    try {
      await connectionsApi.testConnection(connection.id);
      alert('Test message sent!');
      loadConnection();
    } catch (err: any) {
      alert('Failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <IconButton component={Link} to="/dashboard" onClick={(e) => { e.preventDefault(); navigate('/dashboard'); }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" component="h1" flexGrow={1}>
          Connection Details
        </Typography>
        <Button startIcon={<RefreshIcon />} onClick={loadConnection}>
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {loading ? (
        <LinearProgress />
      ) : connection ? (
        <>
          <Card sx={{ mb: 3 }}>
            <Box sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                {connection.name || `Connection ${connection.id}`}
              </Typography>
              <Typography color="text.secondary" gutterBottom>
                Telegram: @{connection.telegram_channel_username || connection.telegram_channel_id}
              </Typography>
              <Typography color="text.secondary" gutterBottom>
                Max Chat: {connection.max_chat_id}
              </Typography>
              <Chip
                icon={connection.is_active ? <CheckCircleIcon /> : <ErrorIcon />}
                label={connection.is_active ? 'Active' : 'Inactive'}
                color={connection.is_active ? 'success' : 'error'}
                size="small"
              />
              <Box sx={{ mt: 2 }}>
                <Button variant="contained" onClick={handleTest}>
                  Test Connection
                </Button>
                <Button color="error" onClick={async () => {
                  if (confirm('Delete this connection?')) {
                    await connectionsApi.deleteConnection(connection.id);
                    navigate('/dashboard');
                  }
                }}>
                  Delete
                </Button>
              </Box>
            </Box>
          </Card>

          <Card>
            <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
              <Typography variant="h6">Post History</Typography>
            </Box>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Telegram ID</TableCell>
                    <TableCell>Max ID</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Time</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {connection.posts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        <Typography color="text.secondary" sx={{ py: 4 }}>
                          No posts yet
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    connection.posts.map((post) => (
                      <TableRow key={post.id}>
                        <TableCell>{post.telegram_message_id || '-'}</TableCell>
                        <TableCell>{post.max_message_id || '-'}</TableCell>
                        <TableCell>{post.content_type}</TableCell>
                        <TableCell>
                          <Chip
                            icon={post.status === 'success' ? <CheckCircleIcon /> : <ErrorIcon />}
                            label={post.status}
                            color={post.status === 'success' ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {new Date(post.created_at).toLocaleString()}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Card>
        </>
      ) : (
        <Alert severity="info">Connection not found</Alert>
      )}
    </Container>
  );
}