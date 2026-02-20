import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Grid,
  IconButton,
  LinearProgress,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Link as LinkIcon,
  Telegram as TelegramIcon,
  ArrowForward as ArrowForwardIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Send as SendIcon,
} from '@mui/icons-material';
import {
  authApi,
  connectionsApi,
  type Connection,
  type TelegramConnection,
  type MaxChannel,
  type User,
} from '../services/api';

export default function Dashboard() {
  const navigate = useNavigate();
  const [connections, setConnections] = useState<Connection[]>([]);
  const [telegramConnections, setTelegramConnections] = useState<TelegramConnection[]>([]);
  const [maxChannels, setMaxChannels] = useState<MaxChannel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [user, setUser] = useState<User | null>(null);
  const [resendingEmail, setResendingEmail] = useState(false);
  const [resendSuccess, setResendSuccess] = useState('');

  // Add Telegram dialog
  const [tgDialogOpen, setTgDialogOpen] = useState(false);
  const [tgUsername, setTgUsername] = useState('');
  const [tgBotToken, setTgBotToken] = useState('');
  const [tgCreating, setTgCreating] = useState(false);

  // Add Max Channel dialog
  const [maxDialogOpen, setMaxDialogOpen] = useState(false);
  const [maxBotToken, setMaxBotToken] = useState('');
  const [maxChatId, setMaxChatId] = useState('');
  const [maxName, setMaxName] = useState('');
  const [maxCreating, setMaxCreating] = useState(false);

  // Add Link dialog
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [linkTgId, setLinkTgId] = useState<number | ''>('');
  const [linkMaxId, setLinkMaxId] = useState<number | ''>('');
  const [linkName, setLinkName] = useState('');
  const [linkCreating, setLinkCreating] = useState(false);

  // Edit Telegram dialog
  const [editTgDialogOpen, setEditTgDialogOpen] = useState(false);
  const [editTgId, setEditTgId] = useState<number | null>(null);
  const [editTgUsername, setEditTgUsername] = useState('');
  const [editTgBotToken, setEditTgBotToken] = useState('');
  const [editTgActive, setEditTgActive] = useState(true);
  const [editTgSaving, setEditTgSaving] = useState(false);

  // Edit Max Channel dialog
  const [editMaxDialogOpen, setEditMaxDialogOpen] = useState(false);
  const [editMaxId, setEditMaxId] = useState<number | null>(null);
  const [editMaxBotToken, setEditMaxBotToken] = useState('');
  const [editMaxChatId, setEditMaxChatId] = useState('');
  const [editMaxName, setEditMaxName] = useState('');
  const [editMaxActive, setEditMaxActive] = useState(true);
  const [editMaxSaving, setEditMaxSaving] = useState(false);

  useEffect(() => { loadAll(); }, []);

  const loadAll = async () => {
    try {
      setLoading(true);
      const [userData, conns, tgConns, maxChs] = await Promise.all([
        authApi.getMe(),
        connectionsApi.listConnections(),
        connectionsApi.listTelegramConnections(),
        connectionsApi.listMaxChannels(),
      ]);
      setUser(userData);
      setConnections(conns);
      setTelegramConnections(tgConns);
      setMaxChannels(maxChs);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  // ── Telegram handlers ──
  const handleCreateTelegram = async () => {
    setTgCreating(true);
    try {
      await connectionsApi.createTelegramConnection(tgUsername, tgBotToken);
      setTgDialogOpen(false);
      setTgUsername(''); setTgBotToken('');
      await loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create Telegram channel');
    } finally { setTgCreating(false); }
  };

  const handleDeleteTelegram = async (id: number) => {
    if (!confirm('Delete this Telegram channel? All linked connections will be removed.')) return;
    try {
      await connectionsApi.deleteTelegramConnection(id);
      await loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete');
    }
  };

  const openEditTgDialog = (tg: TelegramConnection) => {
    setEditTgId(tg.id);
    setEditTgUsername(tg.telegram_channel_username || '');
    setEditTgBotToken('');
    setEditTgActive(tg.is_active);
    setEditTgDialogOpen(true);
  };

  const handleUpdateTelegram = async () => {
    if (!editTgId) return;
    setEditTgSaving(true);
    try {
      const data: any = { is_active: editTgActive };
      if (editTgUsername.trim()) data.telegram_channel_username = editTgUsername.trim();
      if (editTgBotToken.trim()) data.bot_token = editTgBotToken.trim();
      await connectionsApi.updateTelegramConnection(editTgId, data);
      setEditTgDialogOpen(false);
      await loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update');
    } finally { setEditTgSaving(false); }
  };

  // ── Max Channel handlers ──
  const handleCreateMaxChannel = async () => {
    setMaxCreating(true);
    try {
      await connectionsApi.createMaxChannel(maxBotToken, Number(maxChatId), maxName || undefined);
      setMaxDialogOpen(false);
      setMaxBotToken(''); setMaxChatId(''); setMaxName('');
      await loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create Max channel');
    } finally { setMaxCreating(false); }
  };

  const handleDeleteMaxChannel = async (id: number) => {
    if (!confirm('Delete this Max channel? All linked connections will be removed.')) return;
    try {
      await connectionsApi.deleteMaxChannel(id);
      await loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete');
    }
  };

  const handleTestMaxChannel = async (id: number) => {
    try {
      const result = await connectionsApi.testMaxChannel(id);
      alert(result.message);
    } catch (err: any) {
      alert('Error: ' + (err.response?.data?.detail || err.message));
    }
  };

  const openEditMaxDialog = (ch: MaxChannel) => {
    setEditMaxId(ch.id);
    setEditMaxBotToken('');
    setEditMaxChatId(String(ch.chat_id));
    setEditMaxName(ch.name || '');
    setEditMaxActive(ch.is_active);
    setEditMaxDialogOpen(true);
  };

  const handleUpdateMaxChannel = async () => {
    if (!editMaxId) return;
    setEditMaxSaving(true);
    try {
      const data: any = { is_active: editMaxActive };
      if (editMaxBotToken.trim()) data.bot_token = editMaxBotToken.trim();
      if (editMaxChatId.trim()) data.chat_id = Number(editMaxChatId);
      if (editMaxName.trim()) data.name = editMaxName.trim();
      await connectionsApi.updateMaxChannel(editMaxId, data);
      setEditMaxDialogOpen(false);
      await loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update');
    } finally { setEditMaxSaving(false); }
  };

  // ── Link handlers ──
  const handleCreateLink = async () => {
    setLinkCreating(true);
    try {
      await connectionsApi.createConnection(linkTgId as number, linkMaxId as number, linkName || undefined);
      setLinkDialogOpen(false);
      setLinkTgId(''); setLinkMaxId(''); setLinkName('');
      await loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create link');
    } finally { setLinkCreating(false); }
  };

  const handleDeleteLink = async (id: number) => {
    if (!confirm('Delete this link?')) return;
    try {
      await connectionsApi.deleteConnection(id);
      await loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete');
    }
  };

  const canCreateLink = telegramConnections.length > 0 && maxChannels.length > 0 && user?.is_email_verified;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" sx={{ mb: 3 }}>Dashboard</Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>
      )}

      {user && !user.is_email_verified && (
        <Alert severity="warning" sx={{ mb: 2 }} action={
          <Button color="inherit" size="small" disabled={resendingEmail} onClick={async () => {
            setResendingEmail(true);
            try {
              const res = await authApi.resendVerification();
              setResendSuccess(res.message);
            } catch (err: any) {
              setError(err.response?.data?.detail || 'Failed to resend');
            } finally { setResendingEmail(false); }
          }}>
            {resendingEmail ? 'Sending...' : 'Resend'}
          </Button>
        }>
          Please verify your email to create links.
        </Alert>
      )}

      {resendSuccess && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setResendSuccess('')}>{resendSuccess}</Alert>
      )}

      {loading ? <LinearProgress /> : (
        <Grid container spacing={3}>
          {/* Telegram Channels */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TelegramIcon sx={{ color: '#0088cc' }} /> Telegram Channels
                  </Typography>
                  <Button size="small" startIcon={<AddIcon />} onClick={() => setTgDialogOpen(true)}>Add</Button>
                </Box>
                {telegramConnections.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                    No Telegram channels yet
                  </Typography>
                ) : (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {telegramConnections.map((tg) => (
                      <Card key={tg.id} variant="outlined">
                        <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Box>
                              <Typography variant="body2" fontWeight={600}>
                                @{tg.telegram_channel_username || tg.telegram_channel_id}
                              </Typography>
                              <Chip
                                label={tg.is_active ? 'Active' : 'Inactive'}
                                size="small"
                                color={tg.is_active ? 'success' : 'default'}
                                sx={{ height: 18, fontSize: '0.65rem', mt: 0.5 }}
                              />
                            </Box>
                            <Box>
                              <IconButton size="small" onClick={() => openEditTgDialog(tg)}>
                                <EditIcon fontSize="small" />
                              </IconButton>
                              <IconButton size="small" color="error" onClick={() => handleDeleteTelegram(tg.id)}>
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Box>
                          </Box>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Max Channels */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{
                      width: 24, height: 24, borderRadius: '50%', bgcolor: '#7c4dff',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: 'white', fontSize: '0.7rem', fontWeight: 'bold',
                    }}>M</Box>
                    Max Channels
                  </Typography>
                  <Button size="small" startIcon={<AddIcon />} onClick={() => setMaxDialogOpen(true)}>Add</Button>
                </Box>
                {maxChannels.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                    No Max channels yet
                  </Typography>
                ) : (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {maxChannels.map((ch) => (
                      <Card key={ch.id} variant="outlined">
                        <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Box>
                              <Typography variant="body2" fontWeight={600}>
                                {ch.name || `Chat ${ch.chat_id}`}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                ID: {ch.chat_id}
                              </Typography>
                              <Box sx={{ mt: 0.5 }}>
                                <Chip
                                  label={ch.is_active ? 'Active' : 'Inactive'}
                                  size="small"
                                  color={ch.is_active ? 'success' : 'default'}
                                  sx={{ height: 18, fontSize: '0.65rem' }}
                                />
                              </Box>
                            </Box>
                            <Box>
                              <IconButton size="small" onClick={() => handleTestMaxChannel(ch.id)} title="Test">
                                <SendIcon fontSize="small" />
                              </IconButton>
                              <IconButton size="small" onClick={() => openEditMaxDialog(ch)}>
                                <EditIcon fontSize="small" />
                              </IconButton>
                              <IconButton size="small" color="error" onClick={() => handleDeleteMaxChannel(ch.id)}>
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Box>
                          </Box>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Links */}
          <Grid item xs={12}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LinkIcon /> Links
                  </Typography>
                  <Button
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={() => {
                      setLinkTgId(telegramConnections[0]?.id || '');
                      setLinkMaxId(maxChannels[0]?.id || '');
                      setLinkName('');
                      setLinkDialogOpen(true);
                    }}
                    disabled={!canCreateLink}
                  >
                    Add Link
                  </Button>
                </Box>

                {!canCreateLink && connections.length === 0 && (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                    {!user?.is_email_verified
                      ? 'Verify your email first'
                      : telegramConnections.length === 0 && maxChannels.length === 0
                      ? 'Add a Telegram channel and a Max channel first'
                      : telegramConnections.length === 0
                      ? 'Add a Telegram channel first'
                      : 'Add a Max channel first'}
                  </Typography>
                )}

                {connections.length > 0 && (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {connections.map((conn) => (
                      <Card key={conn.id} variant="outlined">
                        <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1, minWidth: 0 }}>
                              <TelegramIcon sx={{ color: '#0088cc', flexShrink: 0, fontSize: 20 }} />
                              <Typography variant="body2" noWrap>
                                @{conn.telegram_channel_username || conn.telegram_channel_id}
                              </Typography>
                            </Box>

                            <ArrowForwardIcon sx={{ color: 'text.disabled', flexShrink: 0 }} />

                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1, minWidth: 0 }}>
                              <Box sx={{
                                width: 20, height: 20, borderRadius: '50%', bgcolor: '#7c4dff',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                flexShrink: 0, color: 'white', fontSize: '0.6rem', fontWeight: 'bold',
                              }}>M</Box>
                              <Typography variant="body2" noWrap>
                                {conn.max_channel_name || `Chat ${conn.max_chat_id}`}
                              </Typography>
                            </Box>

                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexShrink: 0 }}>
                              <Chip
                                icon={conn.is_active ? <CheckCircleIcon /> : <ErrorIcon />}
                                label={conn.is_active ? 'Active' : 'Off'}
                                color={conn.is_active ? 'success' : 'error'}
                                size="small"
                              />
                              <Button size="small" onClick={() => navigate(`/connections/${conn.id}`)}>
                                Details
                              </Button>
                              <IconButton size="small" color="error" onClick={() => handleDeleteLink(conn.id)}>
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Box>
                          </Box>
                          {conn.name && (
                            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                              {conn.name}
                            </Typography>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Add Telegram Channel Dialog */}
      <Dialog open={tgDialogOpen} onClose={() => setTgDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Telegram Channel</DialogTitle>
        <DialogContent>
          <TextField label="Channel Username" placeholder="@yourchannel" fullWidth
            value={tgUsername} onChange={(e) => setTgUsername(e.target.value)} sx={{ mt: 1, mb: 2 }} />
          <TextField label="Bot Token" placeholder="From @BotFather" fullWidth
            value={tgBotToken} onChange={(e) => setTgBotToken(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTgDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateTelegram}
            disabled={tgCreating || !tgUsername.trim() || !tgBotToken.trim()}>
            {tgCreating ? 'Creating...' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Max Channel Dialog */}
      <Dialog open={maxDialogOpen} onClose={() => setMaxDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Max Channel</DialogTitle>
        <DialogContent>
          <TextField label="Bot Token" placeholder="Max bot token" fullWidth
            value={maxBotToken} onChange={(e) => setMaxBotToken(e.target.value)} sx={{ mt: 1, mb: 2 }} />
          <TextField label="Chat ID" placeholder="Max chat/channel ID" fullWidth type="number"
            value={maxChatId} onChange={(e) => setMaxChatId(e.target.value)} sx={{ mb: 2 }} />
          <TextField label="Name (optional)" placeholder="e.g. My Max Channel" fullWidth
            value={maxName} onChange={(e) => setMaxName(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMaxDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateMaxChannel}
            disabled={maxCreating || !maxBotToken.trim() || !maxChatId.trim()}>
            {maxCreating ? 'Creating...' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Link Dialog */}
      <Dialog open={linkDialogOpen} onClose={() => setLinkDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Link</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 1, mb: 2 }}>
            <InputLabel>Telegram Channel</InputLabel>
            <Select value={linkTgId} label="Telegram Channel"
              onChange={(e) => setLinkTgId(e.target.value as number)}>
              {telegramConnections.map((tg) => (
                <MenuItem key={tg.id} value={tg.id}>
                  @{tg.telegram_channel_username || tg.telegram_channel_id}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Max Channel</InputLabel>
            <Select value={linkMaxId} label="Max Channel"
              onChange={(e) => setLinkMaxId(e.target.value as number)}>
              {maxChannels.map((ch) => (
                <MenuItem key={ch.id} value={ch.id}>
                  {ch.name || `Chat ${ch.chat_id}`} (ID: {ch.chat_id})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField label="Link Name (optional)" fullWidth
            value={linkName} onChange={(e) => setLinkName(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLinkDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateLink}
            disabled={linkCreating || !linkTgId || !linkMaxId}>
            {linkCreating ? 'Creating...' : 'Create Link'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Telegram Channel Dialog */}
      <Dialog open={editTgDialogOpen} onClose={() => setEditTgDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Telegram Channel</DialogTitle>
        <DialogContent>
          <TextField label="Channel Username" fullWidth value={editTgUsername}
            onChange={(e) => setEditTgUsername(e.target.value)} sx={{ mt: 1, mb: 2 }} />
          <TextField label="Bot Token (leave empty to keep)" fullWidth value={editTgBotToken}
            onChange={(e) => setEditTgBotToken(e.target.value)} sx={{ mb: 2 }} />
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select value={editTgActive ? 'active' : 'inactive'} label="Status"
              onChange={(e) => setEditTgActive(e.target.value === 'active')}>
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="inactive">Inactive</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditTgDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleUpdateTelegram} disabled={editTgSaving}>
            {editTgSaving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Max Channel Dialog */}
      <Dialog open={editMaxDialogOpen} onClose={() => setEditMaxDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Max Channel</DialogTitle>
        <DialogContent>
          <TextField label="Bot Token (leave empty to keep)" fullWidth value={editMaxBotToken}
            onChange={(e) => setEditMaxBotToken(e.target.value)} sx={{ mt: 1, mb: 2 }} />
          <TextField label="Chat ID" fullWidth type="number" value={editMaxChatId}
            onChange={(e) => setEditMaxChatId(e.target.value)} sx={{ mb: 2 }} />
          <TextField label="Name" fullWidth value={editMaxName}
            onChange={(e) => setEditMaxName(e.target.value)} sx={{ mb: 2 }} />
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select value={editMaxActive ? 'active' : 'inactive'} label="Status"
              onChange={(e) => setEditMaxActive(e.target.value === 'active')}>
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="inactive">Inactive</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditMaxDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleUpdateMaxChannel} disabled={editMaxSaving}>
            {editMaxSaving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
