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
import { useLanguage } from '../i18n/LanguageContext';

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

function HtmlText({ html }: { html: string }) {
  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}

export default function Docs() {
  const theme = useTheme();
  const { t } = useLanguage();

  const stepIcons = [
    [BotIcon, ArrowIcon, CopyIcon],
    [ChannelIcon, SettingsIcon, BotIcon, CheckIcon],
    [ArrowIcon, ArrowIcon, CheckIcon],
  ];

  const maxStepIcons = [
    [BotIcon, ArrowIcon, CopyIcon],
    [ChannelIcon, ArrowIcon, CheckIcon],
    [ArrowIcon, ArrowIcon, CheckIcon],
  ];

  const linkStepIcons = [
    [ArrowIcon, ArrowIcon, ArrowIcon, CheckIcon],
    [ArrowIcon, CheckIcon, ArrowIcon],
  ];

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
            {t.docs.headerTitle}
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.9, mt: 1, fontSize: { xs: '1rem', md: '1.2rem' } }}>
            {t.docs.headerSubtitle}
          </Typography>
        </Container>
      </Box>

      <Container maxWidth="md" sx={{ py: { xs: 4, md: 6 } }}>
        {/* Overview */}
        <Paper elevation={0} sx={{ p: 3, border: '1px solid', borderColor: 'grey.200', borderRadius: 2, mb: 4 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            {t.docs.overview.title}
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            {t.docs.overview.description}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap', justifyContent: 'center', py: 2 }}>
            <Chip icon={<TelegramIcon />} label={t.docs.overview.step1} variant="outlined" />
            <ArrowIcon sx={{ color: 'text.disabled' }} />
            <Chip
              icon={<img src={maxLogo} alt="" width={18} height={18} style={{ borderRadius: 3 }} />}
              label={t.docs.overview.step2}
              variant="outlined"
            />
            <ArrowIcon sx={{ color: 'text.disabled' }} />
            <Chip icon={<LinkIcon />} label={t.docs.overview.step3} variant="outlined" />
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            {t.docs.overview.afterSetup}
          </Typography>
        </Paper>

        <Alert severity="info" sx={{ mb: 4 }}>
          <HtmlText html={t.docs.registerAlert} />
        </Alert>

        {/* ── Step 1: Telegram ── */}
        <SectionTitle icon={<TelegramIcon sx={{ color: '#0088cc', fontSize: 32 }} />}>
          {t.docs.telegramSection.title}
        </SectionTitle>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          {t.docs.telegramSection.description}
        </Typography>

        <Stepper orientation="vertical" sx={{ mb: 4 }}>
          {[t.docs.telegramSection.step1, t.docs.telegramSection.step2, t.docs.telegramSection.step3].map((step, stepIdx) => (
            <Step key={stepIdx} active expanded>
              <StepLabel>
                <Typography fontWeight={600}>{step.title}</Typography>
              </StepLabel>
              <StepContent>
                <List dense disablePadding>
                  {step.items.map((item, itemIdx) => {
                    const IconComponent = stepIcons[stepIdx]?.[itemIdx] || ArrowIcon;
                    return (
                      <ListItem key={itemIdx} disableGutters>
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <IconComponent fontSize="small" color={IconComponent === CheckIcon ? 'success' : undefined} />
                        </ListItemIcon>
                        <ListItemText primary={<HtmlText html={item} />} />
                      </ListItem>
                    );
                  })}
                </List>
              </StepContent>
            </Step>
          ))}
        </Stepper>

        <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 2 }}>
          <HtmlText html={t.docs.telegramSection.warning} />
        </Alert>

        <Divider sx={{ my: 5 }} />

        {/* ── Step 2: Max ── */}
        <SectionTitle
          icon={<img src={maxLogo} alt="Max" width={32} height={32} style={{ borderRadius: 6 }} />}
        >
          {t.docs.maxSection.title}
        </SectionTitle>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          {t.docs.maxSection.description}
        </Typography>

        <Stepper orientation="vertical" sx={{ mb: 4 }}>
          {[t.docs.maxSection.step1, t.docs.maxSection.step2, t.docs.maxSection.step3].map((step, stepIdx) => (
            <Step key={stepIdx} active expanded>
              <StepLabel>
                <Typography fontWeight={600}>{step.title}</Typography>
              </StepLabel>
              <StepContent>
                <List dense disablePadding>
                  {step.items.map((item, itemIdx) => {
                    const IconComponent = maxStepIcons[stepIdx]?.[itemIdx] || ArrowIcon;
                    return (
                      <ListItem key={itemIdx} disableGutters>
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <IconComponent fontSize="small" color={IconComponent === CheckIcon ? 'success' : undefined} />
                        </ListItemIcon>
                        <ListItemText primary={<HtmlText html={item} />} />
                      </ListItem>
                    );
                  })}
                </List>
              </StepContent>
            </Step>
          ))}
        </Stepper>

        <Divider sx={{ my: 5 }} />

        {/* ── Step 3: Link ── */}
        <SectionTitle icon={<LinkIcon sx={{ fontSize: 32, color: theme.palette.secondary.main }} />}>
          {t.docs.linkSection.title}
        </SectionTitle>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          {t.docs.linkSection.description}
        </Typography>

        <Stepper orientation="vertical" sx={{ mb: 4 }}>
          {[t.docs.linkSection.step1, t.docs.linkSection.step2].map((step, stepIdx) => (
            <Step key={stepIdx} active expanded>
              <StepLabel>
                <Typography fontWeight={600}>{step.title}</Typography>
              </StepLabel>
              <StepContent>
                <List dense disablePadding>
                  {step.items.map((item, itemIdx) => {
                    const IconComponent = linkStepIcons[stepIdx]?.[itemIdx] || ArrowIcon;
                    return (
                      <ListItem key={itemIdx} disableGutters>
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <IconComponent fontSize="small" color={IconComponent === CheckIcon ? 'success' : undefined} />
                        </ListItemIcon>
                        <ListItemText primary={<HtmlText html={item} />} />
                      </ListItem>
                    );
                  })}
                </List>
              </StepContent>
            </Step>
          ))}
        </Stepper>

        <Alert severity="info" sx={{ mb: 2 }}>
          {t.docs.linkSection.multipleLinks}
        </Alert>

        <Divider sx={{ my: 5 }} />

        {/* ── Troubleshooting ── */}
        <SectionTitle icon={<SettingsIcon sx={{ fontSize: 32 }} />}>
          {t.docs.troubleshooting.title}
        </SectionTitle>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 4 }}>
          {t.docs.troubleshooting.items.map((item, idx) => (
            <Paper key={idx} elevation={0} sx={{ p: 2.5, border: '1px solid', borderColor: 'grey.200', borderRadius: 2 }}>
              <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                {item.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {item.description}
              </Typography>
            </Paper>
          ))}
        </Box>

        {/* Footer note */}
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 6, mb: 2 }}>
          {t.docs.footerHelp}
        </Typography>
      </Container>
    </Box>
  );
}
