import axios from 'axios';
import type { AxiosRequestConfig, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import type {
  ApiResponse,
  ApiError,
  LoginCredentials,
  LoginResponse,
  PaginatedResponse,
  Url,
  CheckResult,
  Diff,
  NotificationRule,
  AnalyticsData,
  PlatformStats,
  User,
  CreateUrlRequest,
  UpdateUrlRequest,
  CreateCheckRequest,
  CreateNotificationRuleRequest,
  UpdateNotificationRuleRequest,
  PaginationParams,
  UserRole,
} from '../types';
import { useAuthStore } from '../store/authStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    const apiError: ApiError = {
      message: 'Network error',
      statusCode: 500,
    };

    if (error.response) {
      apiError.statusCode = error.response.status;
      apiError.message = error.response.data?.message || 'Request failed';
      apiError.details = error.response.data?.details;
    } else if (error.code === 'ECONNABORTED') {
      apiError.message = 'Request timed out';
    } else if (error.message === 'Network Error') {
      apiError.message = 'Unable to connect to server';
    }

    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
    }

    return Promise.reject(apiError);
  },
);

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    const response = await api.post<ApiResponse<LoginResponse>>('/auth/login', credentials);
    return response.data.data;
  },
  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },
  me: async (): Promise<{ user: User }> => {
    const response = await api.get<ApiResponse<{ user: User }>>('/auth/me');
    return response.data.data;
  },
};

export const urlsApi = {
  list: async (params?: PaginationParams): Promise<PaginatedResponse<Url>> => {
    const response = await api.get<ApiResponse<PaginatedResponse<Url>>>('/urls', { params });
    return response.data.data;
  },
  get: async (id: string): Promise<Url> => {
    const response = await api.get<ApiResponse<Url>>(`/urls/${id}`);
    return response.data.data;
  },
  create: async (data: CreateUrlRequest): Promise<Url> => {
    const response = await api.post<ApiResponse<Url>>('/urls', data);
    return response.data.data;
  },
  update: async (id: string, data: UpdateUrlRequest): Promise<Url> => {
    const response = await api.put<ApiResponse<Url>>(`/urls/${id}`, data);
    return response.data.data;
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/urls/${id}`);
  },
  toggle: async (id: string, enabled: boolean): Promise<Url> => {
    const response = await api.patch<ApiResponse<Url>>(`/urls/${id}/toggle`, { enabled });
    return response.data.data;
  },
  check: async (id: string): Promise<CheckResult> => {
    const response = await api.post<ApiResponse<CheckResult>>(`/urls/${id}/check`);
    return response.data.data;
  },
};

export const checksApi = {
  list: async (urlId?: string, params?: PaginationParams): Promise<PaginatedResponse<CheckResult>> => {
    const queryParams: Record<string, string | number | undefined> = { ...params };
    if (urlId) {
      queryParams.urlId = urlId;
    }
    const response = await api.get<ApiResponse<PaginatedResponse<CheckResult>>>('/checks', { params: queryParams });
    return response.data.data;
  },
  get: async (id: string): Promise<CheckResult> => {
    const response = await api.get<ApiResponse<CheckResult>>(`/checks/${id}`);
    return response.data.data;
  },
  create: async (data: CreateCheckRequest): Promise<CheckResult> => {
    const response = await api.post<ApiResponse<CheckResult>>('/checks', data);
    return response.data.data;
  },
};

export const diffsApi = {
  list: async (urlId?: string, params?: PaginationParams): Promise<PaginatedResponse<Diff>> => {
    const config: AxiosRequestConfig = { params: { ...params } };
    if (urlId) {
      config.params = { ...config.params, urlId };
    }
    const response = await api.get<ApiResponse<PaginatedResponse<Diff>>>('/diffs', config);
    return response.data.data;
  },
  get: async (id: string): Promise<Diff> => {
    const response = await api.get<ApiResponse<Diff>>(`/diffs/${id}`);
    return response.data.data;
  },
  getAiSummary: async (id: string): Promise<{ summary: string }> => {
    const response = await api.get<ApiResponse<{ summary: string }>>(`/diffs/${id}/ai-summary`);
    return response.data.data;
  },
};

export const notificationsApi = {
  list: async (): Promise<NotificationRule[]> => {
    const response = await api.get<ApiResponse<NotificationRule[]>>('/notifications');
    return response.data.data;
  },
  get: async (id: string): Promise<NotificationRule> => {
    const response = await api.get<ApiResponse<NotificationRule>>(`/notifications/${id}`);
    return response.data.data;
  },
  create: async (data: CreateNotificationRuleRequest): Promise<NotificationRule> => {
    const response = await api.post<ApiResponse<NotificationRule>>('/notifications', data);
    return response.data.data;
  },
  update: async (id: string, data: UpdateNotificationRuleRequest): Promise<NotificationRule> => {
    const response = await api.put<ApiResponse<NotificationRule>>(`/notifications/${id}`, data);
    return response.data.data;
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/notifications/${id}`);
  },
};

export const analyticsApi = {
  get: async (urlId: string): Promise<AnalyticsData> => {
    const response = await api.get<ApiResponse<AnalyticsData>>(`/analytics/${urlId}`);
    return response.data.data;
  },
  getPlatformStats: async (): Promise<PlatformStats> => {
    const response = await api.get<ApiResponse<PlatformStats>>('/analytics/platform');
    return response.data.data;
  },
};

export const usersApi = {
  list: async (): Promise<User[]> => {
    const response = await api.get<ApiResponse<User[]>>('/users');
    return response.data.data;
  },
  updateRole: async (id: string, role: UserRole): Promise<User> => {
    const response = await api.patch<ApiResponse<User>>(`/users/${id}/role`, { role });
    return response.data.data;
  },
};

export default api;
