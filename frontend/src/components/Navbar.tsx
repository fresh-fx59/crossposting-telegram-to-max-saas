import { AppBar, Box, Button, Container, IconButton, Toolbar, Typography } from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';
import { useLanguage } from '../i18n/LanguageContext';
import { getStoredValue } from '../services/storage';

export default function Navbar() {
  const navigate = useNavigate();
  const token = getStoredValue('access_token');
  const { language, setLanguage, t } = useLanguage();

  const handleLogout = async () => {
    try {
      await authApi.logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const toggleLanguage = () => {
    setLanguage(language === 'ru' ? 'en' : 'ru');
  };

  return (
    <AppBar position="static" color="default" elevation={0}>
      <Container maxWidth="lg">
        <Toolbar disableGutters>
          <Typography
            variant="h6"
            component={RouterLink}
            to="/"
            sx={{
              flexGrow: 1,
              textDecoration: 'none',
              color: 'inherit',
              fontWeight: 700,
            }}
          >
            {t.nav.brand}
          </Typography>

          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <IconButton
              onClick={toggleLanguage}
              size="small"
              sx={{
                fontSize: '0.85rem',
                fontWeight: 600,
                border: '1px solid',
                borderColor: 'grey.300',
                borderRadius: 1,
                px: 1,
                py: 0.5,
                minWidth: 36,
              }}
            >
              {language === 'ru' ? 'EN' : 'RU'}
            </IconButton>
            <Button color="inherit" component={RouterLink} to="/docs">
              {t.nav.docs}
            </Button>
            {token ? (
              <>
                <Button color="inherit" component={RouterLink} to="/dashboard">
                  {t.nav.dashboard}
                </Button>
                <Button color="inherit" component={RouterLink} to="/account">
                  {t.nav.account}
                </Button>
                <Button color="inherit" onClick={handleLogout}>
                  {t.nav.logout}
                </Button>
              </>
            ) : (
              <>
                <Button color="inherit" component={RouterLink} to="/register">
                  {t.nav.register}
                </Button>
                <Button variant="contained" component={RouterLink} to="/login">
                  {t.nav.login}
                </Button>
              </>
            )}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}
