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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
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

  // Edit connection dialog state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editMaxChatId, setEditMaxChatId] = useState('');
  const [editName, setEditName] = useState('');
  const [editActive, setEditActive] = useState(true);
  const [editSaving, setEditSaving] = useState(false);

  const openEditDialog = () => {
    if (!connection) return;
    setEditMaxChatId(String(connection.max_chat_id));
    setEditName(connection.name || '');
    setEditActive(connection.is_active);
    setEditDialogOpen(true);
  };

  const handleUpdateConnection = async () => {
    if (!connection) return;
    setEditSaving(true);
    try {
      const data: Partial<{ max_chat_id: number; name: string; is_active: boolean }> = {
        is_active: editActive,
      };
      if (editMaxChatId.trim()) data.max_chat_id = Number(editMaxChatId);
      if (editName.trim()) data.name = editName.trim();
      await connectionsApi.updateConnection(connection.id, data);
      setEditDialogOpen(false);
      await loadConnection();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update connection');
    } finally {
      setEditSaving(false);
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
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Button variant="contained" onClick={handleTest}>
                  Test Connection
                </Button>
                <Button variant="outlined" startIcon={<EditIcon />} onClick={openEditDialog}>
                  Edit
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

      {/* Edit Connection Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Connection</DialogTitle>
        <DialogContent>
          <TextField
            label="Max Chat ID"
            fullWidth
            value={editMaxChatId}
            onChange={(e) => setEditMaxChatId(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            label="Link Name"
            fullWidth
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select
              value={editActive ? 'active' : 'inactive'}
              label="Status"
              onChange={(e) => setEditActive(e.target.value === 'active')}
            >
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="inactive">Inactive</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleUpdateConnection} disabled={editSaving}>
            {editSaving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}