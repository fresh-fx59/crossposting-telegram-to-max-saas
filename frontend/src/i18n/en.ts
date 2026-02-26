const en = {
  // Navbar
  nav: {
    brand: 'Telegram Crossposter',
    docs: 'Docs',
    dashboard: 'Dashboard',
    account: 'Account',
    logout: 'Logout',
    register: 'Register',
    login: 'Login',
  },

  // Landing page
  landing: {
    heroTitle: 'Telegram to Max Crossposter',
    heroSubtitle: 'Automate your content sharing across platforms',
    heroDescription:
      'Seamlessly forward posts from your Telegram channels to Max messenger. Set up connections in minutes and let the system handle the rest.',
    getStarted: 'Get Started Free',
    login: 'Login',
    featuresTitle: 'Features',
    features: {
      autoForwarding: {
        title: 'Auto Forwarding',
        description:
          'Automatically forward posts from Telegram channels to Max messenger in real time.',
      },
      richContent: {
        title: 'Rich Content',
        description:
          'Support for text and photo content \u2014 your posts arrive exactly as intended.',
      },
      rateControl: {
        title: 'Rate Control',
        description:
          'Configurable daily post limits so you stay in control of volume.',
      },
      postHistory: {
        title: 'Post History',
        description:
          'Full history of every forwarded post for tracking and debugging.',
      },
      secure: {
        title: 'Secure by Default',
        description:
          'All tokens and credentials are encrypted at rest. Your data stays safe.',
      },
    },
    footer: 'Telegram Crossposter',
    contact: 'Contact us:',
  },

  // Register page
  register: {
    title: 'Create Account',
    email: 'Email',
    password: 'Password',
    passwordHelper: 'Minimum 8 characters',
    confirmPassword: 'Confirm Password',
    submit: 'Register',
    hasAccount: 'Already have an account?',
    loginLink: 'Login',
    successMessage: 'Registration successful! Verification email sent to {email}.',
    redirecting: 'Redirecting to dashboard...',
    errors: {
      passwordsMismatch: 'Passwords do not match',
      passwordTooShort: 'Password must be at least 8 characters',
      captchaRequired: 'Please complete the captcha',
      registrationFailed: 'Registration failed',
    },
  },

  // Login page
  login: {
    title: 'Login',
    email: 'Email',
    password: 'Password',
    submit: 'Login',
    noAccount: "Don't have an account?",
    registerLink: 'Register',
    forgotPassword: 'Forgot password?',
    verificationNeeded:
      'Your email address needs to be verified. Please check your inbox for the verification link.',
    resend: 'Resend',
    sending: 'Sending...',
    errors: {
      captchaRequired: 'Please complete the captcha',
      loginFailed: 'Login failed',
      resendFailed: 'Failed to resend verification email',
    },
  },

  // Verify email page
  verifyEmail: {
    title: 'Email Verification',
    success: 'Email verified successfully! Redirecting to dashboard...',
    verifying: 'Verifying your email address...',
    errors: {
      noToken: 'No verification token provided',
      failed: 'Email verification failed',
    },
  },

  // Dashboard
  dashboard: {
    title: 'Dashboard',
    verifyEmailWarning: 'Please verify your email to create links.',
    resend: 'Resend',
    sending: 'Sending...',
    failedToLoad: 'Failed to load data',
    failedToResend: 'Failed to resend',

    telegram: {
      title: 'Telegram Channels',
      add: 'Add',
      empty: 'No Telegram channels yet',
      active: 'Active',
      inactive: 'Inactive',
      addDialog: {
        title: 'Add Telegram Channel',
        username: 'Channel Username',
        usernamePlaceholder: '@yourchannel',
        botToken: 'Bot Token',
        botTokenPlaceholder: 'From @BotFather',
        cancel: 'Cancel',
        add: 'Add',
        creating: 'Creating...',
      },
      editDialog: {
        title: 'Edit Telegram Channel',
        username: 'Channel Username',
        botToken: 'Bot Token (leave empty to keep)',
        status: 'Status',
        active: 'Active',
        inactive: 'Inactive',
        cancel: 'Cancel',
        save: 'Save',
        saving: 'Saving...',
      },
      errors: {
        createFailed: 'Failed to create Telegram channel',
        deleteFailed: 'Failed to delete',
        updateFailed: 'Failed to update',
      },
      confirmDelete: 'Delete this Telegram channel? All linked connections will be removed.',
    },

    max: {
      title: 'Max Channels',
      add: 'Add',
      empty: 'No Max channels yet',
      active: 'Active',
      inactive: 'Inactive',
      addDialog: {
        title: 'Add Max Channel',
        botToken: 'Bot Token',
        botTokenPlaceholder: 'Max bot token',
        chatId: 'Chat ID',
        chatIdPlaceholder: 'Max chat/channel ID',
        name: 'Name (optional)',
        namePlaceholder: 'e.g. My Max Channel',
        cancel: 'Cancel',
        add: 'Add',
        creating: 'Creating...',
      },
      editDialog: {
        title: 'Edit Max Channel',
        botToken: 'Bot Token (leave empty to keep)',
        chatId: 'Chat ID',
        name: 'Name',
        status: 'Status',
        active: 'Active',
        inactive: 'Inactive',
        cancel: 'Cancel',
        save: 'Save',
        saving: 'Saving...',
      },
      errors: {
        createFailed: 'Failed to create Max channel',
        deleteFailed: 'Failed to delete',
        updateFailed: 'Failed to update',
      },
      confirmDelete: 'Delete this Max channel? All linked connections will be removed.',
    },

    links: {
      title: 'Links',
      addLink: 'Add Link',
      active: 'Active',
      off: 'Off',
      details: 'Details',
      verifyFirst: 'Verify your email first',
      addBoth: 'Add a Telegram channel and a Max channel first',
      addTelegram: 'Add a Telegram channel first',
      addMax: 'Add a Max channel first',
      addDialog: {
        title: 'Add Link',
        telegramChannel: 'Telegram Channel',
        maxChannel: 'Max Channel',
        linkName: 'Link Name (optional)',
        cancel: 'Cancel',
        create: 'Create Link',
        creating: 'Creating...',
      },
      errors: {
        createFailed: 'Failed to create link',
        deleteFailed: 'Failed to delete',
      },
      confirmDelete: 'Delete this link?',
    },
  },

  // Connection Detail page
  connectionDetail: {
    title: 'Connection Details',
    refresh: 'Refresh',
    connectionNotFound: 'Connection not found',
    connectionName: 'Connection {id}',
    telegram: 'Telegram',
    max: 'Max',
    active: 'Active',
    inactive: 'Inactive',
    testConnection: 'Test Connection',
    edit: 'Edit',
    delete: 'Delete',
    testSent: 'Test message sent!',
    testFailed: 'Failed: {error}',
    confirmDelete: 'Delete this connection?',
    failedToLoad: 'Failed to load connection',

    postHistory: {
      title: 'Post History',
      telegramId: 'Telegram ID',
      maxId: 'Max ID',
      type: 'Type',
      status: 'Status',
      error: 'Error',
      time: 'Time',
      empty: 'No posts yet',
    },

    editDialog: {
      title: 'Edit Connection',
      linkName: 'Link Name',
      status: 'Status',
      active: 'Active',
      inactive: 'Inactive',
      cancel: 'Cancel',
      save: 'Save',
      saving: 'Saving...',
      failedToUpdate: 'Failed to update connection',
    },
  },

  // Settings / Account page
  account: {
    title: 'Account',
    info: 'Account Information',
    email: 'Email',
    emailVerified: 'Email verified',
    yes: 'Yes',
    no: 'No',
    connectionsLimit: 'Connections limit',
    dailyPostsLimit: 'Daily posts limit',
    signedUp: 'Signed up',
    logout: 'Logout',
    failedToLoad: 'Failed to load user data',
  },

  // Docs page
  docs: {
    headerTitle: 'Setup Guide',
    headerSubtitle: 'Everything you need to start crossposting from Telegram to Max',

    overview: {
      title: 'How it works',
      description:
        'The Crossposter automatically forwards messages from your Telegram channels to Max messenger. The setup takes three steps:',
      step1: '1. Add Telegram channel',
      step2: '2. Add Max channel',
      step3: '3. Create a link',
      afterSetup:
        'Once linked, every new post in the Telegram channel is automatically forwarded to the Max channel in real time.',
    },

    registerAlert:
      'You need to <strong>register an account</strong> and <strong>verify your email</strong> before you can create links.',

    telegramSection: {
      title: 'Step 1: Add a Telegram Channel',
      description:
        'You need a Telegram bot that is an admin in your channel. The bot receives updates via webhook and forwards them to the Crossposter.',

      step1: {
        title: 'Create a Telegram bot',
        items: [
          'Open Telegram and search for <code>@BotFather</code>',
          'Send <code>/newbot</code> and follow the prompts to name your bot',
          'Copy the <strong>bot token</strong> \u2014 it looks like <code>123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11</code>',
        ],
      },
      step2: {
        title: 'Add the bot as a channel admin',
        items: [
          'Open your Telegram channel settings',
          'Go to <strong>Administrators</strong> \u2192 <strong>Add Administrator</strong>',
          'Search for your bot by username and add it',
          'The bot only needs the default admin permissions (no special permissions required)',
        ],
      },
      step3: {
        title: 'Add the channel in the Dashboard',
        items: [
          'Go to <strong>Dashboard</strong> \u2192 <strong>Telegram Channels</strong> \u2192 click <strong>Add</strong>',
          'Enter your <strong>Channel Username</strong> (e.g. <code>@mychannel</code>) and the <strong>Bot Token</strong> you copied',
          'The system will automatically set up the Telegram webhook for you',
        ],
      },

      warning:
        'Each Telegram bot can only be connected to <strong>one channel</strong> at a time. If you have multiple Telegram channels, create a separate bot for each one.',
    },

    maxSection: {
      title: 'Step 2: Add a Max Channel',
      description:
        'You need a Max bot and a channel (or chat) where the bot will post messages.',

      step1: {
        title: 'Create a Max bot',
        items: [
          'Open Max messenger and find the <strong>@metabot</strong> (the official bot creator)',
          'Follow the prompts to create a new bot',
          'Copy the <strong>bot token</strong> (access token) you receive',
        ],
      },
      step2: {
        title: 'Get the Chat ID',
        items: [
          'Add your Max bot to the channel or chat where you want posts forwarded',
          'The <strong>Chat ID</strong> is the numeric identifier of the channel/chat. You can find it in the channel info or URL',
          'Make sure the bot has permission to post messages in the channel',
        ],
      },
      step3: {
        title: 'Add the channel in the Dashboard',
        items: [
          'Go to <strong>Dashboard</strong> \u2192 <strong>Max Channels</strong> \u2192 click <strong>Add</strong>',
          'Enter the <strong>Bot Token</strong>, <strong>Chat ID</strong>, and optionally a <strong>Name</strong> for easy identification',
          'Use the <strong>Test</strong> button (send icon) to verify the bot can post to the channel',
        ],
      },
    },

    linkSection: {
      title: 'Step 3: Create a Link',
      description:
        'A link connects one Telegram channel to one Max channel. When a new post appears in the Telegram channel, it is automatically forwarded to the linked Max channel.',

      step1: {
        title: 'Create the link',
        items: [
          'Go to <strong>Dashboard</strong> \u2192 <strong>Links</strong> \u2192 click <strong>Add Link</strong>',
          'Select the Telegram channel (source) and Max channel (destination)',
          'Optionally give the link a name for easy identification',
          'Click <strong>Create Link</strong> \u2014 the connection is now live',
        ],
      },
      step2: {
        title: 'Test it',
        items: [
          'Post a message in your Telegram channel',
          'Within seconds, the message should appear in your Max channel',
          'Click <strong>Details</strong> on the link to view post history and check for any errors',
        ],
      },

      multipleLinks:
        'You can create multiple links \u2014 for example, forward one Telegram channel to several Max channels, or connect different Telegram channels to different Max destinations.',
    },

    troubleshooting: {
      title: 'Troubleshooting',
      items: [
        {
          title: 'Messages are not being forwarded',
          description:
            'Check that both the Telegram channel and Max channel show "Active" status on the Dashboard. Make sure the link is also active. Click "Details" on the link to see if posts are arriving with errors.',
        },
        {
          title: '"Test" button on Max channel fails',
          description:
            'Verify that the Bot Token is correct and that the bot has been added to the Max channel with permission to send messages. Double-check the Chat ID.',
        },
        {
          title: 'Telegram webhook not working',
          description:
            'The webhook is set up automatically when you add a Telegram channel. If it stops working, try editing the channel (click the edit icon) and saving without changes \u2014 this will re-register the webhook.',
        },
        {
          title: '"Verify your email first" message',
          description:
            'You must verify your email address before creating links. Check your inbox (and spam folder) for the verification email. You can resend it from the Dashboard.',
        },
        {
          title: 'Daily post limit reached',
          description:
            'Each account has a daily post limit. Once reached, new posts won\'t be forwarded until the next day. Check your limits on the Account page.',
        },
      ],
    },

    footerHelp: 'Need more help? Check the post history in your link details for specific error messages.',
  },

  common: {
    chat: 'Chat',
  },
};

// Deep type that widens all string literals to `string`
type DeepString<T> = T extends string
  ? string
  : T extends readonly (infer U)[]
  ? DeepString<U>[]
  : T extends object
  ? { [K in keyof T]: DeepString<T[K]> }
  : T;

export type Translations = DeepString<typeof en>;
export default en as Translations;
