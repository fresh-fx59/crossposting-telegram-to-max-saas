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
  Stepper,
  Step,
  StepLabel,
  Collapse,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  LinkOff as LinkOffIcon,
  Link as LinkIcon,
  Telegram as TelegramIcon,
  ArrowForward as ArrowForwardIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { authApi, connectionsApi, type Connection, type TelegramConnection, type User } from '../services/api';

export default function Dashboard() {
  const navigate = useNavigate();
  const [connections, setConnections] = useState<Connection[]>([]);
  const [telegramConnections, setTelegramConnections] = useState<TelegramConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [user, setUser] = useState<User | null>(null);
  const [resendingEmail, setResendingEmail] = useState(false);
  const [resendSuccess, setResendSuccess] = useState('');
  const [showTelegramChannels, setShowTelegramChannels] = useState(false);

  // Add Link dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [selectedTgId, setSelectedTgId] = useState<number | 'new'>('new');
  const [newTelegramUsername, setNewTelegramUsername] = useState('');
  const [newBotToken, setNewBotToken] = useState('');
  const [linkMaxChatId, setLinkMaxChatId] = useState('');
  const [linkName, setLinkName] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadData();
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const userData = await authApi.getMe();
      setUser(userData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load user data');
    }
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [conns, tgConns] = await Promise.all([
        connectionsApi.listConnections(),
        connectionsApi.listTelegramConnections(),
      ]);
      setConnections(conns);
      setTelegramConnections(tgConns);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const openDialog = () => {
    setActiveStep(0);
    setSelectedTgId(telegramConnections.length > 0 ? telegramConnections[0].id : 'new');
    setNewTelegramUsername('');
    setNewBotToken('');
    setLinkMaxChatId('');
    setLinkName('');
    setDialogOpen(true);
  };

  const handleCreateLink = async () => {
    setCreating(true);
    try {
      let tgConnId: number;

      if (selectedTgId === 'new') {
        const tgConn = await connectionsApi.createTelegramConnection(newTelegramUsername, newBotToken);
        tgConnId = tgConn.id;
      } else {
        tgConnId = selectedTgId;
      }

      await connectionsApi.createConnection(tgConnId, Number(linkMaxChatId), linkName || undefined);
      setDialogOpen(false);
      await loadData();
      await loadUser();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create link');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteConnection = async (connId: number) => {
    if (!confirm('Delete this link? Posts will no longer be forwarded.')) return;
    try {
      await connectionsApi.deleteConnection(connId);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete link');
    }
  };

  const handleDeleteTelegramChannel = async (tgId: number) => {
    const linkedCount = connections.filter((c) => c.telegram_connection_id === tgId).length;
    const msg = linkedCount > 0
      ? `This channel has ${linkedCount} active link(s). Deleting it will break them. Continue?`
      : 'Delete this Telegram channel?';
    if (!confirm(msg)) return;
    try {
      await connectionsApi.deleteTelegramConnection(tgId);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete channel');
    }
  };

  // Edit Telegram Channel dialog state
  const [editTgDialogOpen, setEditTgDialogOpen] = useState(false);
  const [editTgId, setEditTgId] = useState<number | null>(null);
  const [editTgUsername, setEditTgUsername] = useState('');
  const [editTgBotToken, setEditTgBotToken] = useState('');
  const [editTgActive, setEditTgActive] = useState(true);
  const [editTgSaving, setEditTgSaving] = useState(false);

  const openEditTgDialog = (tg: TelegramConnection) => {
    setEditTgId(tg.id);
    setEditTgUsername(tg.telegram_channel_username || '');
    setEditTgBotToken('');
    setEditTgActive(tg.is_active);
    setEditTgDialogOpen(true);
  };

  const handleUpdateTelegramChannel = async () => {
    if (!editTgId) return;
    setEditTgSaving(true);
    try {
      const data: Partial<{ telegram_channel_username: string; bot_token: string; is_active: boolean }> = {};
      if (editTgUsername.trim()) data.telegram_channel_username = editTgUsername.trim();
      if (editTgBotToken.trim()) data.bot_token = editTgBotToken.trim();
      data.is_active = editTgActive;
      await connectionsApi.updateTelegramConnection(editTgId, data);
      setEditTgDialogOpen(false);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update Telegram channel');
    } finally {
      setEditTgSaving(false);
    }
  };

  const canProceedStep0 = selectedTgId !== 'new' || (newTelegramUsername.trim() !== '' && newBotToken.trim() !== '');
  const canProceedStep1 = linkMaxChatId.trim() !== '';

  const steps = ['Telegram Source', 'Max Destination'];

  // Find which telegram channel a connection belongs to
  const getTgChannel = (conn: Connection) =>
    telegramConnections.find((tg) => tg.id === conn.telegram_connection_id);

  // Telegram channels not linked to any connection
  const unlinkedTgChannels = telegramConnections.filter(
    (tg) => !connections.some((c) => c.telegram_connection_id === tg.id)
  );

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Crosspost Links
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={openDialog}
          disabled={!user?.is_email_verified || !user?.max_token_set}
        >
          Add Link
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {user && !user.is_email_verified && (
        <Alert
          severity="warning"
          sx={{ mb: 2 }}
          action={
            <Button
              color="inherit"
              size="small"
              disabled={resendingEmail}
              onClick={async () => {
                setResendingEmail(true);
                setResendSuccess('');
                try {
                  const res = await authApi.resendVerification();
                  setResendSuccess(res.message);
                } catch (err: any) {
                  setError(err.response?.data?.detail || 'Failed to resend verification email');
                } finally {
                  setResendingEmail(false);
                }
              }}
            >
              {resendingEmail ? 'Sending...' : 'Resend'}
            </Button>
          }
        >
          Please verify your email address to create links.
        </Alert>
      )}

      {user && user.is_email_verified && !user.max_token_set && (
        <Alert
          severity="info"
          sx={{ mb: 2 }}
          action={
            <Button color="inherit" size="small" onClick={() => navigate('/settings')}>
              Go to Settings
            </Button>
          }
        >
          Set up your Max bot token in Settings before creating links.
        </Alert>
      )}

      {resendSuccess && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setResendSuccess('')}>
          {resendSuccess}
        </Alert>
      )}

      {loading ? (
        <LinearProgress />
      ) : (
        <>
          {/* Links */}
          {connections.length === 0 ? (
            <Card sx={{ bgcolor: 'action.hover' }}>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <LinkIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No crosspost links yet
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Create a link to forward posts from a Telegram channel to a Max channel.
                </Typography>
              </CardContent>
            </Card>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {connections.map((conn) => {
                const tg = getTgChannel(conn);
                return (
                  <Card key={conn.id}>
                    <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                        {/* Telegram side */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0, flex: 1 }}>
                          <TelegramIcon sx={{ color: '#0088cc', flexShrink: 0 }} />
                          <Box sx={{ minWidth: 0 }}>
                            <Typography variant="subtitle2" noWrap>
                              @{conn.telegram_channel_username || conn.telegram_channel_id}
                            </Typography>
                            {tg && (
                              <Chip
                                label={tg.webhook_url ? 'Webhook active' : 'No webhook'}
                                size="small"
                                variant="outlined"
                                color={tg.webhook_url ? 'success' : 'warning'}
                                sx={{ height: 20, fontSize: '0.7rem' }}
                              />
                            )}
                          </Box>
                        </Box>

                        {/* Arrow */}
                        <ArrowForwardIcon sx={{ color: 'text.disabled', flexShrink: 0 }} />

                        {/* Max side */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0, flex: 1 }}>
                          <Box
                            sx={{
                              width: 24,
                              height: 24,
                              borderRadius: '50%',
                              bgcolor: '#7c4dff',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              flexShrink: 0,
                              color: 'white',
                              fontSize: '0.7rem',
                              fontWeight: 'bold',
                            }}
                          >
                            M
                          </Box>
                          <Typography variant="subtitle2" noWrap>
                            Chat {conn.max_chat_id}
                          </Typography>
                        </Box>

                        {/* Status & actions */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexShrink: 0 }}>
                          <Chip
                            icon={conn.is_active ? <CheckCircleIcon /> : <ErrorIcon />}
                            label={conn.is_active ? 'Active' : 'Inactive'}
                            color={conn.is_active ? 'success' : 'error'}
                            size="small"
                          />
                          <Button
                            size="small"
                            onClick={() => navigate(`/connections/${conn.id}`)}
                          >
                            Details
                          </Button>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteConnection(conn.id)}
                          >
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
                );
              })}
            </Box>
          )}

          {/* Telegram Channels section (collapsible) */}
          {telegramConnections.length > 0 && (
            <Box sx={{ mt: 4 }}>
              <Button
                size="small"
                startIcon={showTelegramChannels ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                onClick={() => setShowTelegramChannels(!showTelegramChannels)}
                sx={{ color: 'text.secondary', textTransform: 'none' }}
              >
                Telegram Channels ({telegramConnections.length})
                {unlinkedTgChannels.length > 0 && (
                  <Chip
                    label={`${unlinkedTgChannels.length} unlinked`}
                    size="small"
                    color="warning"
                    sx={{ ml: 1, height: 20, fontSize: '0.7rem' }}
                  />
                )}
              </Button>
              <Collapse in={showTelegramChannels}>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 1 }}>
                  {telegramConnections.map((tg) => {
                    const linkedConns = connections.filter((c) => c.telegram_connection_id === tg.id);
                    return (
                      <Card key={tg.id} variant="outlined">
                        <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <TelegramIcon sx={{ color: '#0088cc', fontSize: 20 }} />
                              <Typography variant="body2">
                                @{tg.telegram_channel_username || tg.telegram_channel_id}
                              </Typography>
                              <Chip
                                label={tg.is_active ? 'Active' : 'Inactive'}
                                size="small"
                                color={tg.is_active ? 'success' : 'default'}
                                sx={{ height: 20, fontSize: '0.7rem' }}
                              />
                              {linkedConns.length > 0 ? (
                                <Chip
                                  icon={<LinkIcon sx={{ fontSize: '14px !important' }} />}
                                  label={`${linkedConns.length} link(s)`}
                                  size="small"
                                  variant="outlined"
                                  sx={{ height: 20, fontSize: '0.7rem' }}
                                />
                              ) : (
                                <Chip
                                  icon={<LinkOffIcon sx={{ fontSize: '14px !important' }} />}
                                  label="Not linked"
                                  size="small"
                                  color="warning"
                                  variant="outlined"
                                  sx={{ height: 20, fontSize: '0.7rem' }}
                                />
                              )}
                            </Box>
                            <IconButton
                              size="small"
                              onClick={() => openEditTgDialog(tg)}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteTelegramChannel(tg.id)}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Box>
                        </CardContent>
                      </Card>
                    );
                  })}
                </Box>
              </Collapse>
            </Box>
          )}
        </>
      )}

      {/* Add Link Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Crosspost Link</DialogTitle>
        <DialogContent>
          <Stepper activeStep={activeStep} sx={{ mb: 3, mt: 1 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {activeStep === 0 && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Choose an existing Telegram channel or add a new one.
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Telegram Channel</InputLabel>
                <Select
                  value={selectedTgId}
                  label="Telegram Channel"
                  onChange={(e) => setSelectedTgId(e.target.value as number | 'new')}
                >
                  {telegramConnections.map((tg) => (
                    <MenuItem key={tg.id} value={tg.id}>
                      @{tg.telegram_channel_username || tg.telegram_channel_id}
                    </MenuItem>
                  ))}
                  <MenuItem value="new">+ Add new channel</MenuItem>
                </Select>
              </FormControl>

              {selectedTgId === 'new' && (
                <>
                  <TextField
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
                </>
              )}
            </Box>
          )}

          {activeStep === 1 && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Specify the Max chat where posts will be forwarded.
              </Typography>

              <TextField
                label="Max Chat ID"
                placeholder="Target chat ID in Max"
                fullWidth
                value={linkMaxChatId}
                onChange={(e) => setLinkMaxChatId(e.target.value)}
                sx={{ mb: 2 }}
              />

              <TextField
                label="Link Name (optional)"
                placeholder="e.g. News channel → Max team chat"
                fullWidth
                value={linkName}
                onChange={(e) => setLinkName(e.target.value)}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          {activeStep > 0 && (
            <Button onClick={() => setActiveStep(activeStep - 1)}>Back</Button>
          )}
          {activeStep < steps.length - 1 ? (
            <Button
              variant="contained"
              onClick={() => setActiveStep(activeStep + 1)}
              disabled={!canProceedStep0}
            >
              Next
            </Button>
          ) : (
            <Button
              variant="contained"
              onClick={handleCreateLink}
              disabled={!canProceedStep1 || creating}
            >
              {creating ? 'Creating...' : 'Create Link'}
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Edit Telegram Channel Dialog */}
      <Dialog open={editTgDialogOpen} onClose={() => setEditTgDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Telegram Channel</DialogTitle>
        <DialogContent>
          <TextField
            label="Channel Username"
            placeholder="@yourchannel"
            fullWidth
            value={editTgUsername}
            onChange={(e) => setEditTgUsername(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            label="Bot Token (leave empty to keep current)"
            placeholder="From @BotFather"
            fullWidth
            value={editTgBotToken}
            onChange={(e) => setEditTgBotToken(e.target.value)}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select
              value={editTgActive ? 'active' : 'inactive'}
              label="Status"
              onChange={(e) => setEditTgActive(e.target.value === 'active')}
            >
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="inactive">Inactive</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditTgDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleUpdateTelegramChannel} disabled={editTgSaving}>
            {editTgSaving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
