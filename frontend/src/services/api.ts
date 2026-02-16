/** API service for backend communication. */

import axios, { AxiosError, type AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Types
export interface User {
  id: number;
  email: string;
  max_token_set: boolean;
  max_chat_id: number | null;
  connections_limit: number;
  daily_posts_limit: number;
  is_email_verified: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

export interface TelegramConnection {
  id: number;
  telegram_channel_id: number;
  telegram_channel_username: string | null;
  webhook_url: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Connection {
  id: number;
  telegram_connection_id: number;
  telegram_channel_id: number;
  telegram_channel_username: string | null;
  max_chat_id: number;
  name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Post {
  id: number;
  connection_id: number;
  telegram_message_id: number | null;
  max_message_id: string | null;
  content_type: string;
  status: string;
  error_message: string | null;
  created_at: string;
}

export interface ConnectionDetail extends Connection {
  posts: Post[];
}

// Auth API
export const authApi = {
  register: async (email: string, password: string, captchaToken: string): Promise<AuthTokens> => {
    const response = await api.post<AuthTokens>('/auth/register', {
      email,
      password,
      captcha_token: captchaToken,
    });
    return response.data;
  },

  login: async (email: string, password: string, captchaToken: string): Promise<AuthTokens> => {
    const response = await api.post<AuthTokens>('/auth/login', {
      email,
      password,
      captcha_token: captchaToken,
    });
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
    localStorage.removeItem('access_token');
  },

  verifyEmail: async (token: string): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/verify-email', { token });
    return response.data;
  },

  resendVerification: async (): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/resend-verification');
    return response.data;
  },

  forgotPassword: async (email: string, captchaToken: string): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/forgot-password', {
      email,
      captcha_token: captchaToken,
    });
    return response.data;
  },

  resetPassword: async (token: string, newPassword: string): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/reset-password', {
      token,
      new_password: newPassword,
    });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};

// Connections API
export const connectionsApi = {
  // Telegram connections
  createTelegramConnection: async (
    telegramChannelUsername: string,
    botToken: string
  ): Promise<TelegramConnection> => {
    const response = await api.post<TelegramConnection>('/api/connections/telegram', {
      telegram_channel_username: telegramChannelUsername,
      bot_token: botToken,
    });
    return response.data;
  },

  listTelegramConnections: async (): Promise<TelegramConnection[]> => {
    const response = await api.get<TelegramConnection[]>('/api/connections/telegram');
    return response.data;
  },

  updateTelegramConnection: async (
    id: number,
    data: Partial<{ telegram_channel_username: string; bot_token: string; is_active: boolean }>
  ): Promise<TelegramConnection> => {
    const response = await api.put<TelegramConnection>(`/api/connections/telegram/${id}`, data);
    return response.data;
  },

  deleteTelegramConnection: async (id: number): Promise<void> => {
    await api.delete(`/api/connections/telegram/${id}`);
  },

  // Connections
  createConnection: async (
    telegramConnectionId: number,
    maxChatId: number,
    name?: string
  ): Promise<Connection> => {
    const response = await api.post<Connection>('/api/connections', {
      telegram_connection_id: telegramConnectionId,
      max_chat_id: maxChatId,
      name,
    });
    return response.data;
  },

  listConnections: async (): Promise<Connection[]> => {
    const response = await api.get<Connection[]>('/api/connections');
    return response.data;
  },

  getConnection: async (id: number, page: number = 1, pageSize: number = 20): Promise<ConnectionDetail> => {
    const response = await api.get<ConnectionDetail>(`/api/connections/${id}`, {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  updateConnection: async (
    id: number,
    data: Partial<{ max_chat_id: number; name: string; is_active: boolean }>
  ): Promise<Connection> => {
    const response = await api.put<Connection>(`/api/connections/${id}`, data);
    return response.data;
  },

  deleteConnection: async (id: number): Promise<void> => {
    await api.delete(`/api/connections/${id}`);
  },

  testConnection: async (id: number, testMessage?: string): Promise<{
    success: boolean;
    message: string;
    telegram_webhook_info: unknown;
  }> => {
    const response = await api.post(`/api/connections/${id}/test`, null, {
      params: testMessage ? { test_message: testMessage } : {},
    });
    return response.data;
  },
};

// Users API
export const usersApi = {
  updateMe: async (maxToken: string | null = null, maxChatId: number | null = null): Promise<User> => {
    const response = await api.put<User>('/api/users/me', {
      max_token: maxToken,
      max_chat_id: maxChatId,
    });
    return response.data;
  },

  testMax: async (testMessage: string = 'Test message from Telegram Crossposter'): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/api/users/me/test-max', null, {
      params: { test_message: testMessage },
    });
    return response.data;
  },
};

export default api;