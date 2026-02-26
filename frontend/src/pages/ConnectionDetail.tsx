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
import { useLanguage } from '../i18n/LanguageContext';

export default function ConnectionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useLanguage();
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
      setError(err.response?.data?.detail || t.connectionDetail.failedToLoad);
    } finally {
      setLoading(false);
    }
  };

  // Edit connection dialog state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editName, setEditName] = useState('');
  const [editActive, setEditActive] = useState(true);
  const [editSaving, setEditSaving] = useState(false);

  const openEditDialog = () => {
    if (!connection) return;
    setEditName(connection.name || '');
    setEditActive(connection.is_active);
    setEditDialogOpen(true);
  };

  const handleUpdateConnection = async () => {
    if (!connection) return;
    setEditSaving(true);
    try {
      const data: Partial<{ name: string; is_active: boolean }> = {
        is_active: editActive,
      };
      if (editName.trim()) data.name = editName.trim();
      await connectionsApi.updateConnection(connection.id, data);
      setEditDialogOpen(false);
      await loadConnection();
    } catch (err: any) {
      setError(err.response?.data?.detail || t.connectionDetail.editDialog.failedToUpdate);
    } finally {
      setEditSaving(false);
    }
  };

  const handleTest = async () => {
    if (!connection) return;
    try {
      await connectionsApi.testConnection(connection.id);
      alert(t.connectionDetail.testSent);
      loadConnection();
    } catch (err: any) {
      alert(t.connectionDetail.testFailed.replace('{error}', err.response?.data?.detail || err.message));
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <IconButton component={Link} to="/dashboard" onClick={(e) => { e.preventDefault(); navigate('/dashboard'); }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" component="h1" flexGrow={1}>
          {t.connectionDetail.title}
        </Typography>
        <Button startIcon={<RefreshIcon />} onClick={loadConnection}>
          {t.connectionDetail.refresh}
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
                {connection.name || t.connectionDetail.connectionName.replace('{id}', String(connection.id))}
              </Typography>
              <Typography color="text.secondary" gutterBottom>
                {t.connectionDetail.telegram}: @{connection.telegram_channel_username || connection.telegram_channel_id}
              </Typography>
              <Typography color="text.secondary" gutterBottom>
                {t.connectionDetail.max}: {connection.max_channel_name || `${t.common.chat} ${connection.max_chat_id}`}
              </Typography>
              <Chip
                icon={connection.is_active ? <CheckCircleIcon /> : <ErrorIcon />}
                label={connection.is_active ? t.connectionDetail.active : t.connectionDetail.inactive}
                color={connection.is_active ? 'success' : 'error'}
                size="small"
              />
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Button variant="contained" onClick={handleTest}>
                  {t.connectionDetail.testConnection}
                </Button>
                <Button variant="outlined" startIcon={<EditIcon />} onClick={openEditDialog}>
                  {t.connectionDetail.edit}
                </Button>
                <Button color="error" onClick={async () => {
                  if (confirm(t.connectionDetail.confirmDelete)) {
                    await connectionsApi.deleteConnection(connection.id);
                    navigate('/dashboard');
                  }
                }}>
                  {t.connectionDetail.delete}
                </Button>
              </Box>
            </Box>
          </Card>

          <Card>
            <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
              <Typography variant="h6">{t.connectionDetail.postHistory.title}</Typography>
            </Box>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>{t.connectionDetail.postHistory.telegramId}</TableCell>
                    <TableCell>{t.connectionDetail.postHistory.maxId}</TableCell>
                    <TableCell>{t.connectionDetail.postHistory.type}</TableCell>
                    <TableCell>{t.connectionDetail.postHistory.status}</TableCell>
                    <TableCell>{t.connectionDetail.postHistory.error}</TableCell>
                    <TableCell>{t.connectionDetail.postHistory.time}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {connection.posts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        <Typography color="text.secondary" sx={{ py: 4 }}>
                          {t.connectionDetail.postHistory.empty}
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
                          {post.error_message ? (
                            <Typography variant="body2" color="error" sx={{ maxWidth: 300, fontSize: '0.8rem' }}>
                              {post.error_message}
                            </Typography>
                          ) : '-'}
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
        <Alert severity="info">{t.connectionDetail.connectionNotFound}</Alert>
      )}

      {/* Edit Connection Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t.connectionDetail.editDialog.title}</DialogTitle>
        <DialogContent>
          <TextField
            label={t.connectionDetail.editDialog.linkName}
            fullWidth
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
          />
          <FormControl fullWidth>
            <InputLabel>{t.connectionDetail.editDialog.status}</InputLabel>
            <Select
              value={editActive ? 'active' : 'inactive'}
              label={t.connectionDetail.editDialog.status}
              onChange={(e) => setEditActive(e.target.value === 'active')}
            >
              <MenuItem value="active">{t.connectionDetail.editDialog.active}</MenuItem>
              <MenuItem value="inactive">{t.connectionDetail.editDialog.inactive}</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>{t.connectionDetail.editDialog.cancel}</Button>
          <Button variant="contained" onClick={handleUpdateConnection} disabled={editSaving}>
            {editSaving ? t.connectionDetail.editDialog.saving : t.connectionDetail.editDialog.save}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
