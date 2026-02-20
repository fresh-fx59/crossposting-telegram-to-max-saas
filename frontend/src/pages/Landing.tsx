import {
  Box,
  Button,
  Container,
  Grid,
  Paper,
  Stack,
  Typography,
  useTheme,
} from '@mui/material';
import {
  AutorenewRounded,
  PhotoLibraryRounded,
  SpeedRounded,
  HistoryRounded,
  LockRounded,
} from '@mui/icons-material';
import { Link as RouterLink } from 'react-router-dom';

const features = [
  {
    icon: AutorenewRounded,
    title: 'Auto Forwarding',
    description: 'Automatically forward posts from Telegram channels to Max messenger in real time.',
  },
  {
    icon: PhotoLibraryRounded,
    title: 'Rich Content',
    description: 'Support for text and photo content — your posts arrive exactly as intended.',
  },
  {
    icon: SpeedRounded,
    title: 'Rate Control',
    description: 'Configurable daily post limits so you stay in control of volume.',
  },
  {
    icon: HistoryRounded,
    title: 'Post History',
    description: 'Full history of every forwarded post for tracking and debugging.',
  },
  {
    icon: LockRounded,
    title: 'Secure by Default',
    description: 'All tokens and credentials are encrypted at rest. Your data stays safe.',
  },
];

export default function Landing() {
  const theme = useTheme();

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Hero */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          py: { xs: 8, md: 12 },
          textAlign: 'center',
        }}
      >
        <Container maxWidth="md">
          <Typography
            variant="h2"
            component="h1"
            gutterBottom
            fontWeight="bold"
            sx={{ fontSize: { xs: '2rem', md: '3rem' } }}
          >
            Telegram to Max Crossposter
          </Typography>

          <Typography
            variant="h5"
            sx={{ opacity: 0.95, mb: 2, fontSize: { xs: '1.1rem', md: '1.4rem' } }}
          >
            Automate your content sharing across platforms
          </Typography>

          <Typography
            variant="body1"
            sx={{ mb: 5, opacity: 0.85, fontSize: '1.05rem', maxWidth: 520, mx: 'auto' }}
          >
            Seamlessly forward posts from your Telegram channels to Max messenger.
            Set up connections in minutes and let the system handle the rest.
          </Typography>

          <Stack direction="row" spacing={2} justifyContent="center" flexWrap="wrap">
            <Button
              component={RouterLink}
              to="/register"
              variant="contained"
              size="large"
              sx={{
                bgcolor: 'white',
                color: theme.palette.primary.main,
                fontWeight: 600,
                '&:hover': { bgcolor: 'grey.100' },
                px: 4,
                py: 1.5,
              }}
            >
              Get Started Free
            </Button>
            <Button
              component={RouterLink}
              to="/login"
              variant="outlined"
              size="large"
              sx={{
                borderColor: 'rgba(255,255,255,0.7)',
                color: 'white',
                fontWeight: 600,
                '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' },
                px: 4,
                py: 1.5,
              }}
            >
              Login
            </Button>
          </Stack>
        </Container>
      </Box>

      {/* Features */}
      <Box sx={{ flexGrow: 1, py: { xs: 6, md: 10 }, bgcolor: 'grey.50' }}>
        <Container maxWidth="lg">
          <Typography
            variant="h4"
            component="h2"
            textAlign="center"
            fontWeight="bold"
            sx={{ mb: 6 }}
          >
            Features
          </Typography>

          <Grid container spacing={3} justifyContent="center">
            {features.map((f) => (
              <Grid item xs={12} sm={6} md={4} key={f.title}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 3,
                    height: '100%',
                    textAlign: 'center',
                    border: '1px solid',
                    borderColor: 'grey.200',
                    borderRadius: 2,
                  }}
                >
                  <f.icon sx={{ fontSize: 40, color: 'primary.main', mb: 1.5 }} />
                  <Typography variant="h6" gutterBottom fontWeight={600}>
                    {f.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {f.description}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Footer */}
      <Box component="footer" sx={{ py: 3, textAlign: 'center', bgcolor: 'grey.100' }}>
        <Typography variant="body2" color="text.secondary">
          © {new Date().getFullYear()} Telegram Crossposter
        </Typography>
      </Box>
    </Box>
  );
}
