import {
  AppBar,
  Box,
  Button,
  Container,
  Drawer,
  IconButton,
  Stack,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import MenuRoundedIcon from '@mui/icons-material/MenuRounded';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';
import { useLanguage } from '../i18n/LanguageContext';
import { getStoredValue } from '../services/storage';
import { useMemo, useState } from 'react';

export default function Navbar() {
  const navigate = useNavigate();
  const token = getStoredValue('access_token');
  const { language, setLanguage, t } = useLanguage();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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

  const navItems = useMemo(
    () =>
      token
        ? [
            { label: t.nav.docs, to: '/docs' },
            { label: t.nav.dashboard, to: '/dashboard' },
            { label: t.nav.account, to: '/account' },
          ]
        : [
            { label: t.nav.docs, to: '/docs' },
            { label: t.nav.register, to: '/register' },
            { label: t.nav.login, to: '/login', variant: 'contained' as const },
          ],
    [token, t],
  );

  const closeMobileMenu = () => setMobileMenuOpen(false);

  return (
    <AppBar position="static" color="default" elevation={0}>
      <Container maxWidth="lg">
        <Toolbar disableGutters sx={{ minHeight: { xs: 56, sm: 64 } }}>
          <Typography
            variant="h6"
            component={RouterLink}
            to="/"
            sx={{
              flexGrow: 1,
              textDecoration: 'none',
              color: 'inherit',
              fontWeight: 700,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              pr: 1,
            }}
          >
            {t.nav.brand}
          </Typography>

          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
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

            {isMobile ? (
              <>
                <IconButton
                  onClick={() => setMobileMenuOpen(true)}
                  aria-label="Open navigation menu"
                  edge="end"
                  color="inherit"
                >
                  <MenuRoundedIcon />
                </IconButton>
                <Drawer
                  anchor="right"
                  open={mobileMenuOpen}
                  onClose={closeMobileMenu}
                  PaperProps={{ sx: { width: 280, p: 2 } }}
                >
                  <Stack spacing={1}>
                    {navItems.map((item) => (
                      <Button
                        key={item.label}
                        component={RouterLink}
                        to={item.to}
                        onClick={closeMobileMenu}
                        color="inherit"
                        variant={item.variant ?? 'text'}
                        sx={{ justifyContent: 'flex-start' }}
                      >
                        {item.label}
                      </Button>
                    ))}
                    {token && (
                      <Button
                        color="inherit"
                        onClick={() => {
                          closeMobileMenu();
                          handleLogout();
                        }}
                        sx={{ justifyContent: 'flex-start' }}
                      >
                        {t.nav.logout}
                      </Button>
                    )}
                  </Stack>
                </Drawer>
              </>
            ) : (
              <>
                {navItems.map((item) => (
                  <Button
                    key={item.label}
                    color="inherit"
                    component={RouterLink}
                    to={item.to}
                    variant={item.variant ?? 'text'}
                  >
                    {item.label}
                  </Button>
                ))}
                {token && (
                  <Button color="inherit" onClick={handleLogout}>
                    {t.nav.logout}
                  </Button>
                )}
              </>
            )}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}
