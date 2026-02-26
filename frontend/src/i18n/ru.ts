import type { Translations } from './en';

const ru: Translations = {
  // Navbar
  nav: {
    brand: 'Telegram Кросспостер',
    docs: 'Документация',
    dashboard: 'Панель управления',
    account: 'Аккаунт',
    logout: 'Выйти',
    register: 'Регистрация',
    login: 'Войти',
  },

  // Landing page
  landing: {
    heroTitle: 'Кросспостинг из Telegram в Max',
    heroSubtitle: 'Автоматизируйте публикации между платформами',
    heroDescription:
      'Автоматическая пересылка постов из ваших Telegram-каналов в мессенджер Max. Настройте связи за несколько минут \u2014 система сделает всё остальное.',
    getStarted: 'Начать бесплатно',
    login: 'Войти',
    featuresTitle: 'Возможности',
    features: {
      autoForwarding: {
        title: 'Автопересылка',
        description:
          'Автоматическая пересылка постов из Telegram-каналов в мессенджер Max в реальном времени.',
      },
      richContent: {
        title: 'Разный контент',
        description:
          'Поддержка текста и фотографий \u2014 ваши посты доставляются именно так, как задумано.',
      },
      rateControl: {
        title: 'Контроль частоты',
        description:
          'Настраиваемые дневные лимиты публикаций для контроля объёма.',
      },
      postHistory: {
        title: 'История публикаций',
        description:
          'Полная история каждого пересланного поста для отслеживания и отладки.',
      },
      secure: {
        title: 'Безопасность',
        description:
          'Все токены и учётные данные зашифрованы. Ваши данные в безопасности.',
      },
    },
    footer: 'Telegram Кросспостер',
    contact: 'Связаться с нами:',
  },

  // Register page
  register: {
    title: 'Создать аккаунт',
    email: 'Email',
    password: 'Пароль',
    passwordHelper: 'Минимум 8 символов',
    confirmPassword: 'Подтвердите пароль',
    submit: 'Зарегистрироваться',
    hasAccount: 'Уже есть аккаунт?',
    loginLink: 'Войти',
    successMessage: 'Регистрация успешна! Письмо для подтверждения отправлено на {email}.',
    redirecting: 'Перенаправление на панель управления...',
    errors: {
      passwordsMismatch: 'Пароли не совпадают',
      passwordTooShort: 'Пароль должен содержать минимум 8 символов',
      captchaRequired: 'Пожалуйста, пройдите капчу',
      registrationFailed: 'Ошибка регистрации',
    },
  },

  // Login page
  login: {
    title: 'Вход',
    email: 'Email',
    password: 'Пароль',
    submit: 'Войти',
    noAccount: 'Нет аккаунта?',
    registerLink: 'Зарегистрироваться',
    forgotPassword: 'Забыли пароль?',
    verificationNeeded:
      'Ваш email-адрес должен быть подтверждён. Проверьте входящие письма \u2014 там должна быть ссылка для подтверждения.',
    resend: 'Отправить повторно',
    sending: 'Отправка...',
    errors: {
      captchaRequired: 'Пожалуйста, пройдите капчу',
      loginFailed: 'Ошибка входа',
      resendFailed: 'Не удалось отправить письмо повторно',
    },
  },

  // Verify email page
  verifyEmail: {
    title: 'Подтверждение email',
    success: 'Email успешно подтверждён! Перенаправление на панель управления...',
    verifying: 'Подтверждение вашего email-адреса...',
    errors: {
      noToken: 'Токен подтверждения не предоставлен',
      failed: 'Ошибка подтверждения email',
    },
  },

  // Dashboard
  dashboard: {
    title: 'Панель управления',
    verifyEmailWarning: 'Пожалуйста, подтвердите email для создания связей.',
    resend: 'Отправить повторно',
    sending: 'Отправка...',
    failedToLoad: 'Не удалось загрузить данные',
    failedToResend: 'Не удалось отправить повторно',

    telegram: {
      title: 'Telegram-каналы',
      add: 'Добавить',
      empty: 'Telegram-каналов пока нет',
      active: 'Активен',
      inactive: 'Неактивен',
      addDialog: {
        title: 'Добавить Telegram-канал',
        username: 'Имя канала',
        usernamePlaceholder: '@yourchannel',
        botToken: 'Токен бота',
        botTokenPlaceholder: 'От @BotFather',
        cancel: 'Отмена',
        add: 'Добавить',
        creating: 'Создание...',
      },
      editDialog: {
        title: 'Редактировать Telegram-канал',
        username: 'Имя канала',
        botToken: 'Токен бота (оставьте пустым, чтобы не менять)',
        status: 'Статус',
        active: 'Активен',
        inactive: 'Неактивен',
        cancel: 'Отмена',
        save: 'Сохранить',
        saving: 'Сохранение...',
      },
      errors: {
        createFailed: 'Не удалось создать Telegram-канал',
        deleteFailed: 'Не удалось удалить',
        updateFailed: 'Не удалось обновить',
      },
      confirmDelete: 'Удалить этот Telegram-канал? Все связанные подключения будут удалены.',
    },

    max: {
      title: 'Max-каналы',
      add: 'Добавить',
      empty: 'Max-каналов пока нет',
      active: 'Активен',
      inactive: 'Неактивен',
      addDialog: {
        title: 'Добавить Max-канал',
        botToken: 'Токен бота',
        botTokenPlaceholder: 'Токен бота Max',
        chatId: 'Chat ID',
        chatIdPlaceholder: 'ID чата/канала Max',
        name: 'Название (необязательно)',
        namePlaceholder: 'Например, Мой Max-канал',
        cancel: 'Отмена',
        add: 'Добавить',
        creating: 'Создание...',
      },
      editDialog: {
        title: 'Редактировать Max-канал',
        botToken: 'Токен бота (оставьте пустым, чтобы не менять)',
        chatId: 'Chat ID',
        name: 'Название',
        status: 'Статус',
        active: 'Активен',
        inactive: 'Неактивен',
        cancel: 'Отмена',
        save: 'Сохранить',
        saving: 'Сохранение...',
      },
      errors: {
        createFailed: 'Не удалось создать Max-канал',
        deleteFailed: 'Не удалось удалить',
        updateFailed: 'Не удалось обновить',
      },
      confirmDelete: 'Удалить этот Max-канал? Все связанные подключения будут удалены.',
    },

    links: {
      title: 'Связи',
      addLink: 'Добавить связь',
      active: 'Активна',
      off: 'Выкл',
      details: 'Подробнее',
      verifyFirst: 'Сначала подтвердите email',
      addBoth: 'Сначала добавьте Telegram-канал и Max-канал',
      addTelegram: 'Сначала добавьте Telegram-канал',
      addMax: 'Сначала добавьте Max-канал',
      addDialog: {
        title: 'Добавить связь',
        telegramChannel: 'Telegram-канал',
        maxChannel: 'Max-канал',
        linkName: 'Название связи (необязательно)',
        cancel: 'Отмена',
        create: 'Создать связь',
        creating: 'Создание...',
      },
      errors: {
        createFailed: 'Не удалось создать связь',
        deleteFailed: 'Не удалось удалить',
      },
      confirmDelete: 'Удалить эту связь?',
    },
  },

  // Connection Detail page
  connectionDetail: {
    title: 'Детали подключения',
    refresh: 'Обновить',
    connectionNotFound: 'Подключение не найдено',
    connectionName: 'Подключение {id}',
    telegram: 'Telegram',
    max: 'Max',
    active: 'Активно',
    inactive: 'Неактивно',
    testConnection: 'Тестировать',
    edit: 'Редактировать',
    delete: 'Удалить',
    testSent: 'Тестовое сообщение отправлено!',
    testFailed: 'Ошибка: {error}',
    confirmDelete: 'Удалить это подключение?',
    failedToLoad: 'Не удалось загрузить подключение',

    postHistory: {
      title: 'История публикаций',
      telegramId: 'Telegram ID',
      maxId: 'Max ID',
      type: 'Тип',
      status: 'Статус',
      error: 'Ошибка',
      time: 'Время',
      empty: 'Публикаций пока нет',
    },

    editDialog: {
      title: 'Редактировать подключение',
      linkName: 'Название связи',
      status: 'Статус',
      active: 'Активно',
      inactive: 'Неактивно',
      cancel: 'Отмена',
      save: 'Сохранить',
      saving: 'Сохранение...',
      failedToUpdate: 'Не удалось обновить подключение',
    },
  },

  // Settings / Account page
  account: {
    title: 'Аккаунт',
    info: 'Информация об аккаунте',
    email: 'Email',
    emailVerified: 'Email подтверждён',
    yes: 'Да',
    no: 'Нет',
    connectionsLimit: 'Лимит подключений',
    dailyPostsLimit: 'Дневной лимит публикаций',
    signedUp: 'Дата регистрации',
    logout: 'Выйти',
    failedToLoad: 'Не удалось загрузить данные пользователя',
  },

  // Docs page
  docs: {
    headerTitle: 'Руководство по настройке',
    headerSubtitle: 'Всё, что нужно для начала кросспостинга из Telegram в Max',

    overview: {
      title: 'Как это работает',
      description:
        'Кросспостер автоматически пересылает сообщения из ваших Telegram-каналов в мессенджер Max. Настройка состоит из трёх шагов:',
      step1: '1. Добавить Telegram-канал',
      step2: '2. Добавить Max-канал',
      step3: '3. Создать связь',
      afterSetup:
        'После настройки связи каждый новый пост в Telegram-канале автоматически пересылается в Max-канал в реальном времени.',
    },

    registerAlert:
      'Для создания связей необходимо <strong>зарегистрировать аккаунт</strong> и <strong>подтвердить email</strong>.',

    telegramSection: {
      title: 'Шаг 1: Добавить Telegram-канал',
      description:
        'Вам нужен Telegram-бот, который является администратором вашего канала. Бот получает обновления через webhook и пересылает их в Кросспостер.',

      step1: {
        title: 'Создайте Telegram-бота',
        items: [
          'Откройте Telegram и найдите <code>@BotFather</code>',
          'Отправьте <code>/newbot</code> и следуйте инструкциям для создания бота',
          'Скопируйте <strong>токен бота</strong> \u2014 он выглядит как <code>123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11</code>',
        ],
      },
      step2: {
        title: 'Добавьте бота как администратора канала',
        items: [
          'Откройте настройки вашего Telegram-канала',
          'Перейдите в <strong>Администраторы</strong> \u2192 <strong>Добавить администратора</strong>',
          'Найдите вашего бота по имени пользователя и добавьте его',
          'Боту достаточно стандартных прав администратора (специальные разрешения не требуются)',
        ],
      },
      step3: {
        title: 'Добавьте канал в Панели управления',
        items: [
          'Перейдите в <strong>Панель управления</strong> \u2192 <strong>Telegram-каналы</strong> \u2192 нажмите <strong>Добавить</strong>',
          'Введите <strong>Имя канала</strong> (например, <code>@mychannel</code>) и скопированный <strong>Токен бота</strong>',
          'Система автоматически настроит Telegram webhook',
        ],
      },

      warning:
        'Каждый Telegram-бот может быть подключён только к <strong>одному каналу</strong>. Если у вас несколько Telegram-каналов, создайте отдельного бота для каждого.',
    },

    maxSection: {
      title: 'Шаг 2: Добавить Max-канал',
      description:
        'Вам нужен Max-бот и канал (или чат), в который бот будет публиковать сообщения.',

      step1: {
        title: 'Создайте Max-бота',
        items: [
          'Откройте мессенджер Max и найдите <strong>@metabot</strong> (официальный создатель ботов)',
          'Следуйте инструкциям для создания нового бота',
          'Скопируйте полученный <strong>токен бота</strong> (access token)',
        ],
      },
      step2: {
        title: 'Получите Chat ID',
        items: [
          'Добавьте вашего Max-бота в канал или чат, куда хотите пересылать посты',
          '<strong>Chat ID</strong> \u2014 это числовой идентификатор канала/чата. Его можно найти в информации о канале или в URL',
          'Убедитесь, что у бота есть разрешение на отправку сообщений в канал',
        ],
      },
      step3: {
        title: 'Добавьте канал в Панели управления',
        items: [
          'Перейдите в <strong>Панель управления</strong> \u2192 <strong>Max-каналы</strong> \u2192 нажмите <strong>Добавить</strong>',
          'Введите <strong>Токен бота</strong>, <strong>Chat ID</strong> и, при желании, <strong>Название</strong> для удобства',
          'Используйте кнопку <strong>Тест</strong> (иконка отправки), чтобы проверить, что бот может писать в канал',
        ],
      },
    },

    linkSection: {
      title: 'Шаг 3: Создать связь',
      description:
        'Связь соединяет один Telegram-канал с одним Max-каналом. Когда в Telegram-канале появляется новый пост, он автоматически пересылается в связанный Max-канал.',

      step1: {
        title: 'Создайте связь',
        items: [
          'Перейдите в <strong>Панель управления</strong> \u2192 <strong>Связи</strong> \u2192 нажмите <strong>Добавить связь</strong>',
          'Выберите Telegram-канал (источник) и Max-канал (назначение)',
          'При желании дайте связи название для удобства',
          'Нажмите <strong>Создать связь</strong> \u2014 подключение теперь активно',
        ],
      },
      step2: {
        title: 'Протестируйте',
        items: [
          'Опубликуйте сообщение в вашем Telegram-канале',
          'В течение нескольких секунд сообщение должно появиться в Max-канале',
          'Нажмите <strong>Подробнее</strong> на связи, чтобы просмотреть историю публикаций и проверить ошибки',
        ],
      },

      multipleLinks:
        'Вы можете создавать несколько связей \u2014 например, пересылать один Telegram-канал в несколько Max-каналов или соединять разные Telegram-каналы с разными Max-назначениями.',
    },

    troubleshooting: {
      title: 'Решение проблем',
      items: [
        {
          title: 'Сообщения не пересылаются',
          description:
            'Проверьте, что Telegram-канал и Max-канал показывают статус "Активен" на Панели управления. Убедитесь, что связь тоже активна. Нажмите "Подробнее" на связи, чтобы увидеть, приходят ли посты с ошибками.',
        },
        {
          title: 'Кнопка "Тест" для Max-канала не работает',
          description:
            'Проверьте правильность токена бота и убедитесь, что бот добавлен в Max-канал с разрешением на отправку сообщений. Перепроверьте Chat ID.',
        },
        {
          title: 'Telegram webhook не работает',
          description:
            'Webhook настраивается автоматически при добавлении Telegram-канала. Если он перестал работать, попробуйте отредактировать канал (нажмите иконку редактирования) и сохранить без изменений \u2014 это перерегистрирует webhook.',
        },
        {
          title: 'Сообщение "Сначала подтвердите email"',
          description:
            'Для создания связей необходимо подтвердить email-адрес. Проверьте входящие письма (и папку "Спам") на наличие письма с подтверждением. Повторную отправку можно сделать из Панели управления.',
        },
        {
          title: 'Достигнут дневной лимит публикаций',
          description:
            'У каждого аккаунта есть дневной лимит публикаций. После его достижения новые посты не будут пересылаться до следующего дня. Проверьте ваши лимиты на странице Аккаунта.',
        },
      ],
    },

    footerHelp: 'Нужна помощь? Проверьте историю публикаций в деталях связи для конкретных сообщений об ошибках.',
  },

  common: {
    chat: 'Чат',
  },
};

export default ru;
