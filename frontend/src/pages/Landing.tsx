import {
  Box,
  Button,
  Container,
  Stack,
  Typography,
  useTheme,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

export default function Landing() {
  const theme = useTheme();

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Container maxWidth="lg" sx={{ flexGrow: 1, display: 'flex', alignItems: 'center' }}>
        <Box
          sx={{
            maxWidth: 600,
            color: 'white',
            textAlign: 'center',
          }}
        >
          <Typography variant="h2" component="h1" gutterBottom fontWeight="bold">
            Telegram to Max Crossposter
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ opacity: 0.95 }}>
            Automate your content sharing across platforms
          </Typography>

          <Typography variant="body1" sx={{ mb: 6, opacity: 0.9, fontSize: '1.1rem' }}>
            Seamlessly forward posts from your Telegram channels to Max messenger.
            Set up connections in minutes and let our SaaS handle the rest.
          </Typography>

          <Stack direction="row" spacing={3} justifyContent="center" sx={{ mb: 8 }}>
            <Button
              component={RouterLink}
              to="/register"
              variant="contained"
              size="large"
              sx={{
                bgcolor: 'white',
                color: theme.palette.primary.main,
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
                borderColor: 'white',
                color: 'white',
                '&:hover': { borderColor: 'grey.300', bgcolor: 'rgba(255,255,255,0.1)' },
                px: 4,
                py: 1.5,
              }}
            >
              Login
            </Button>
          </Stack>

          <Box sx={{ mt: 8, py: 4, bgcolor: 'rgba(255,255,255,0.1)', borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Features
            </Typography>
            <Box component="ul" sx={{ textAlign: 'left', display: 'inline-block', pl: 2 }}>
              <Typography component="li" sx={{ mb: 1 }}>
                Automatic post forwarding from Telegram channels
              </Typography>
              <Typography component="li" sx={{ mb: 1 }}>
                Support for text and photo content
              </Typography>
              <Typography component="li" sx={{ mb: 1 }}>
                Daily post limits to manage volume
              </Typography>
              <Typography component="li" sx={{ mb: 1 }}>
                Post history for tracking and debugging
              </Typography>
              <Typography component="li" sx={{ mb: 0 }}>
                Secure token encryption
              </Typography>
            </Box>
          </Box>
        </Box>
      </Container>

      <Box component="footer" sx={{ py: 2, textAlign: 'center', opacity: 0.7, color: 'white' }}>
        <Typography variant="body2">
          © 2024 Telegram Crossposter. All rights reserved.
        </Typography>
      </Box>
    </Box>
  );
}