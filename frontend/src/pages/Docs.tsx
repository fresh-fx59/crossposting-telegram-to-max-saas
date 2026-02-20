import {
  Box,
  Container,
  Typography,
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  useTheme,
} from '@mui/material';
import {
  Telegram as TelegramIcon,
  Link as LinkIcon,
  CheckCircle as CheckIcon,
  ArrowForward as ArrowIcon,
  Warning as WarningIcon,
  ContentCopy as CopyIcon,
  SmartToy as BotIcon,
  Forum as ChannelIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import maxLogo from '../assets/max-logo.png';

function Code({ children }: { children: string }) {
  return (
    <Box
      component="code"
      sx={{
        bgcolor: 'grey.100',
        px: 0.8,
        py: 0.3,
        borderRadius: 0.5,
        fontSize: '0.85em',
        fontFamily: 'monospace',
        wordBreak: 'break-all',
      }}
    >
      {children}
    </Box>
  );
}

function SectionTitle({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <Typography
      variant="h5"
      component="h2"
      fontWeight={700}
      sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3, mt: 6 }}
    >
      {icon}
      {children}
    </Typography>
  );
}

export default function Docs() {
  const theme = useTheme();

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'grey.50' }}>
      {/* Header */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          py: { xs: 5, md: 7 },
          textAlign: 'center',
        }}
      >
        <Container maxWidth="md">
          <Typography
            variant="h3"
            component="h1"
            fontWeight="bold"
            sx={{ fontSize: { xs: '1.8rem', md: '2.5rem' } }}
          >
            Setup Guide
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.9, mt: 1, fontSize: { xs: '1rem', md: '1.2rem' } }}>
            Everything you need to start crossposting from Telegram to Max
          </Typography>
        </Container>
      </Box>

      <Container maxWidth="md" sx={{ py: { xs: 4, md: 6 } }}>
        {/* Overview */}
        <Paper elevation={0} sx={{ p: 3, border: '1px solid', borderColor: 'grey.200', borderRadius: 2, mb: 4 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            How it works
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            The Crossposter automatically forwards messages from your Telegram channels to Max messenger.
            The setup takes three steps:
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap', justifyContent: 'center', py: 2 }}>
            <Chip icon={<TelegramIcon />} label="1. Add Telegram channel" variant="outlined" />
            <ArrowIcon sx={{ color: 'text.disabled' }} />
            <Chip
              icon={<img src={maxLogo} alt="" width={18} height={18} style={{ borderRadius: 3 }} />}
              label="2. Add Max channel"
              variant="outlined"
            />
            <ArrowIcon sx={{ color: 'text.disabled' }} />
            <Chip icon={<LinkIcon />} label="3. Create a link" variant="outlined" />
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Once linked, every new post in the Telegram channel is automatically forwarded to the Max channel in real time.
          </Typography>
        </Paper>

        <Alert severity="info" sx={{ mb: 4 }}>
          You need to <strong>register an account</strong> and <strong>verify your email</strong> before you can create links.
        </Alert>

        {/* ── Step 1: Telegram ── */}
        <SectionTitle icon={<TelegramIcon sx={{ color: '#0088cc', fontSize: 32 }} />}>
          Step 1: Add a Telegram Channel
        </SectionTitle>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          You need a Telegram bot that is an admin in your channel. The bot receives updates via webhook
          and forwards them to the Crossposter.
        </Typography>

        <Stepper orientation="vertical" sx={{ mb: 4 }}>
          <Step active expanded>
            <StepLabel>
              <Typography fontWeight={600}>Create a Telegram bot</Typography>
            </StepLabel>
            <StepContent>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><BotIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary={<>Open Telegram and search for <Code>@BotFather</Code></>}
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ArrowIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary={<>Send <Code>/newbot</Code> and follow the prompts to name your bot</>}
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><CopyIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary={<>Copy the <strong>bot token</strong> — it looks like <Code>123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11</Code></>}
                  />
                </ListItem>
              </List>
            </StepContent>
          </Step>

          <Step active expanded>
            <StepLabel>
              <Typography fontWeight={600}>Add the bot as a channel admin</Typography>
            </StepLabel>
            <StepContent>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ChannelIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Open your Telegram channel settings" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><SettingsIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary={<>Go to <strong>Administrators</strong> → <strong>Add Administrator</strong></>} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><BotIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Search for your bot by username and add it" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><CheckIcon fontSize="small" color="success" /></ListItemIcon>
                  <ListItemText primary="The bot only needs the default admin permissions (no special permissions required)" />
                </ListItem>
              </List>
            </StepContent>
          </Step>

          <Step active expanded>
            <StepLabel>
              <Typography fontWeight={600}>Add the channel in the Dashboard</Typography>
            </StepLabel>
            <StepContent>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ArrowIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary={<>Go to <strong>Dashboard</strong> → <strong>Telegram Channels</strong> → click <strong>Add</strong></>}
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ArrowIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary={<>Enter your <strong>Channel Username</strong> (e.g. <Code>@mychannel</Code>) and the <strong>Bot Token</strong> you copied</>}
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><CheckIcon fontSize="small" color="success" /></ListItemIcon>
                  <ListItemText primary="The system will automatically set up the Telegram webhook for you" />
                </ListItem>
              </List>
            </StepContent>
          </Step>
        </Stepper>

        <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 2 }}>
          Each Telegram bot can only be connected to <strong>one channel</strong> at a time. If you have multiple
          Telegram channels, create a separate bot for each one.
        </Alert>

        <Divider sx={{ my: 5 }} />

        {/* ── Step 2: Max ── */}
        <SectionTitle
          icon={<img src={maxLogo} alt="Max" width={32} height={32} style={{ borderRadius: 6 }} />}
        >
          Step 2: Add a Max Channel
        </SectionTitle>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          You need a Max bot and a channel (or chat) where the bot will post messages.
        </Typography>

        <Stepper orientation="vertical" sx={{ mb: 4 }}>
          <Step active expanded>
            <StepLabel>
              <Typography fontWeight={600}>Create a Max bot</Typography>
            </StepLabel>
            <StepContent>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><BotIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary={<>Open Max messenger and find the <strong>@metabot</strong> (the official bot creator)</>}
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ArrowIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Follow the prompts to create a new bot" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><CopyIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary={<>Copy the <strong>bot token</strong> (access token) you receive</>}
                  />
                </ListItem>
              </List>
            </StepContent>
          </Step>

          <Step active expanded>
            <StepLabel>
              <Typography fontWeight={600}>Get the Chat ID</Typography>
            </StepLabel>
            <StepContent>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ChannelIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary="Add your Max bot to the channel or chat where you want posts forwarded"
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ArrowIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary={<>The <strong>Chat ID</strong> is the numeric identifier of the channel/chat. You can find it in the channel info or URL</>}
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><CheckIcon fontSize="small" color="success" /></ListItemIcon>
                  <ListItemText primary="Make sure the bot has permission to post messages in the channel" />
                </ListItem>
              </List>
            </StepContent>
          </Step>

          <Step active expanded>
            <StepLabel>
              <Typography fontWeight={600}>Add the channel in the Dashboard</Typography>
            </StepLabel>
            <StepContent>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ArrowIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary={<>Go to <strong>Dashboard</strong> → <strong>Max Channels</strong> → click <strong>Add</strong></>}
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ArrowIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary={<>Enter the <strong>Bot Token</strong>, <strong>Chat ID</strong>, and optionally a <strong>Name</strong> for easy identification</>}
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><CheckIcon fontSize="small" color="success" /></ListItemIcon>
                  <ListItemText
                    primary={<>Use the <strong>Test</strong> button (send icon) to verify the bot can post to the channel</>}
                  />
                </ListItem>
              </List>
            </StepContent>
          </Step>
        </Stepper>

        <Divider sx={{ my: 5 }} />

        {/* ── Step 3: Link ── */}
        <SectionTitle icon={<LinkIcon sx={{ fontSize: 32, color: theme.palette.secondary.main }} />}>
          Step 3: Create a Link
        </SectionTitle>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          A link connects one Telegram channel to one Max channel. When a new post appears in the Telegram
          channel, it is automatically forwarded to the linked Max channel.
        </Typography>

        <Stepper orientation="vertical" sx={{ mb: 4 }}>
          <Step active expanded>
            <StepLabel>
              <Typography fontWeight={600}>Create the link</Typography>
            </StepLabel>
            <StepContent>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ArrowIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary={<>Go to <strong>Dashboard</strong> → <strong>Links</strong> → click <strong>Add Link</strong></>}
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ArrowIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Select the Telegram channel (source) and Max channel (destination)" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ArrowIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Optionally give the link a name for easy identification" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><CheckIcon fontSize="small" color="success" /></ListItemIcon>
                  <ListItemText primary={<>Click <strong>Create Link</strong> — the connection is now live</>} />
                </ListItem>
              </List>
            </StepContent>
          </Step>

          <Step active expanded>
            <StepLabel>
              <Typography fontWeight={600}>Test it</Typography>
            </StepLabel>
            <StepContent>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ArrowIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Post a message in your Telegram channel" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><CheckIcon fontSize="small" color="success" /></ListItemIcon>
                  <ListItemText primary="Within seconds, the message should appear in your Max channel" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><ArrowIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary={<>Click <strong>Details</strong> on the link to view post history and check for any errors</>}
                  />
                </ListItem>
              </List>
            </StepContent>
          </Step>
        </Stepper>

        <Alert severity="info" sx={{ mb: 2 }}>
          You can create multiple links — for example, forward one Telegram channel to several Max channels,
          or connect different Telegram channels to different Max destinations.
        </Alert>

        <Divider sx={{ my: 5 }} />

        {/* ── Troubleshooting ── */}
        <SectionTitle icon={<SettingsIcon sx={{ fontSize: 32 }} />}>
          Troubleshooting
        </SectionTitle>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 4 }}>
          <Paper elevation={0} sx={{ p: 2.5, border: '1px solid', borderColor: 'grey.200', borderRadius: 2 }}>
            <Typography variant="subtitle2" fontWeight={700} gutterBottom>
              Messages are not being forwarded
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Check that both the Telegram channel and Max channel show "Active" status on the Dashboard.
              Make sure the link is also active. Click "Details" on the link to see if posts are arriving
              with errors.
            </Typography>
          </Paper>

          <Paper elevation={0} sx={{ p: 2.5, border: '1px solid', borderColor: 'grey.200', borderRadius: 2 }}>
            <Typography variant="subtitle2" fontWeight={700} gutterBottom>
              "Test" button on Max channel fails
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Verify that the Bot Token is correct and that the bot has been added to the Max channel
              with permission to send messages. Double-check the Chat ID.
            </Typography>
          </Paper>

          <Paper elevation={0} sx={{ p: 2.5, border: '1px solid', borderColor: 'grey.200', borderRadius: 2 }}>
            <Typography variant="subtitle2" fontWeight={700} gutterBottom>
              Telegram webhook not working
            </Typography>
            <Typography variant="body2" color="text.secondary">
              The webhook is set up automatically when you add a Telegram channel. If it stops working,
              try editing the channel (click the edit icon) and saving without changes — this will
              re-register the webhook.
            </Typography>
          </Paper>

          <Paper elevation={0} sx={{ p: 2.5, border: '1px solid', borderColor: 'grey.200', borderRadius: 2 }}>
            <Typography variant="subtitle2" fontWeight={700} gutterBottom>
              "Verify your email first" message
            </Typography>
            <Typography variant="body2" color="text.secondary">
              You must verify your email address before creating links. Check your inbox (and spam folder)
              for the verification email. You can resend it from the Dashboard.
            </Typography>
          </Paper>

          <Paper elevation={0} sx={{ p: 2.5, border: '1px solid', borderColor: 'grey.200', borderRadius: 2 }}>
            <Typography variant="subtitle2" fontWeight={700} gutterBottom>
              Daily post limit reached
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Each account has a daily post limit. Once reached, new posts won't be forwarded until the
              next day. Check your limits on the Account page.
            </Typography>
          </Paper>
        </Box>

        {/* Footer note */}
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 6, mb: 2 }}>
          Need more help? Check the post history in your link details for specific error messages.
        </Typography>
      </Container>
    </Box>
  );
}
