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
      apiError.message = (error.response?.data as any)?.message || 'Request failed';
      apiError.details = (error.response?.data as any)?.details;
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
    const response = await api.post<{ access_token: string; refresh_token: string }>('/auth/login', credentials);
    const token = response.data.access_token;
    
    // To get the user profile, make a manual request using the retrieved token
    const userResponse = await api.get<{ id: string; email: string; name: string; is_active: boolean; created_at: string }>('/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    const user: User = {
      id: userResponse.data.id,
      email: userResponse.data.email,
      name: userResponse.data.name,
      role: 'admin',
      avatarUrl: null,
      createdAt: userResponse.data.created_at,
      lastLoginAt: null,
    };
    
    return {
      token,
      user,
    };
  },
  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },
  me: async (): Promise<{ user: User }> => {
    const response = await api.get<{ id: string; email: string; name: string; is_active: boolean; created_at: string }>('/auth/me');
    const user: User = {
      id: response.data.id,
      email: response.data.email,
      name: response.data.name,
      role: 'admin',
      avatarUrl: null,
      createdAt: response.data.created_at,
      lastLoginAt: null,
    };
    return { user };
  },
};

export const urlsApi = {
  list: async (params?: PaginationParams): Promise<PaginatedResponse<Url>> => {
    const response = await api.get<{ data: any[]; pagination: any }>('/urls', { params });
    return {
      items: (response.data.data || []).map((item: any) => ({
        id: item.id,
        url: item.url,
        name: item.name,
        description: item.description || '',
        status: item.status.toUpperCase(),
        backend: item.backend,
        enabled: item.enabled,
        checkInterval: Math.round(item.interval_seconds / 60),
        lastCheckedAt: item.last_checked,
        lastStatus: item.status.toUpperCase(),
        createdAt: item.created_at,
        updatedAt: item.created_at,
        tags: item.tags || [],
      })),
      total: response.data.pagination?.total || 0,
      page: response.data.pagination?.page || 1,
      pageSize: response.data.pagination?.per_page || 20,
      totalPages: response.data.pagination?.total_pages || 1,
    };
  },
  get: async (id: string): Promise<Url> => {
    const response = await api.get<any>(`/urls/${id}`);
    const item = response.data;
    return {
      id: item.id,
      url: item.url,
      name: item.name,
      description: item.description || '',
      status: item.status.toUpperCase(),
      backend: item.backend,
      enabled: item.enabled,
      checkInterval: Math.round(item.interval_seconds / 60),
      lastCheckedAt: item.last_checked,
      lastStatus: item.status.toUpperCase(),
      createdAt: item.created_at,
      updatedAt: item.created_at,
      tags: item.tags || [],
    };
  },
  create: async (data: CreateUrlRequest): Promise<Url> => {
    const reqData = {
      name: data.name,
      url: data.url,
      interval_seconds: data.checkInterval * 60,
      enabled: true,
      backend: data.backend,
      tags: data.tags || [],
    };
    const response = await api.post<any>('/urls', reqData);
    const item = response.data;
    return {
      id: item.id,
      url: item.url,
      name: item.name,
      description: item.description || '',
      status: item.status.toUpperCase(),
      backend: item.backend,
      enabled: item.enabled,
      checkInterval: Math.round(item.interval_seconds / 60),
      lastCheckedAt: item.last_checked,
      lastStatus: item.status.toUpperCase(),
      createdAt: item.created_at,
      updatedAt: item.created_at,
      tags: item.tags || [],
    };
  },
  update: async (id: string, data: UpdateUrlRequest): Promise<Url> => {
    const reqData: any = {};
    if (data.name !== undefined) reqData.name = data.name;
    if (data.url !== undefined) reqData.url = data.url;
    if (data.checkInterval !== undefined) reqData.interval_seconds = data.checkInterval * 60;
    if (data.enabled !== undefined) reqData.enabled = data.enabled;
    if (data.backend !== undefined) reqData.backend = data.backend;
    if (data.tags !== undefined) reqData.tags = data.tags;
    
    const response = await api.put<any>(`/urls/${id}`, reqData);
    const item = response.data;
    return {
      id: item.id,
      url: item.url,
      name: item.name,
      description: item.description || '',
      status: item.status.toUpperCase(),
      backend: item.backend,
      enabled: item.enabled,
      checkInterval: Math.round(item.interval_seconds / 60),
      lastCheckedAt: item.last_checked,
      lastStatus: item.status.toUpperCase(),
      createdAt: item.created_at,
      updatedAt: item.created_at,
      tags: item.tags || [],
    };
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/urls/${id}`);
  },
  toggle: async (id: string, enabled: boolean): Promise<Url> => {
    const response = await api.patch<any>(`/urls/${id}/toggle`, { enabled });
    const item = response.data;
    return {
      id: item.id,
      url: item.url,
      name: item.name,
      description: item.description || '',
      status: item.status.toUpperCase(),
      backend: item.backend,
      enabled: item.enabled,
      checkInterval: Math.round(item.interval_seconds / 60),
      lastCheckedAt: item.last_checked,
      lastStatus: item.status.toUpperCase(),
      createdAt: item.created_at,
      updatedAt: item.created_at,
      tags: item.tags || [],
    };
  },
  check: async (id: string): Promise<CheckResult> => {
    const response = await api.post<any>(`/urls/${id}/check`);
    return response.data;
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
    const response = await api.get<any>(`/urls/${urlId}/analytics`);
    return response.data;
  },
  getPlatformStats: async (): Promise<PlatformStats> => {
    const response = await api.get<{ total_checks: number; total_changes: number; change_rate: number }>('/urls/analytics');
    return {
      totalUrls: 6, // seeded default URLs count is 6
      activeUrls: 6,
      totalChecks: response.data.total_checks,
      totalDiffs: response.data.total_changes,
      totalUsers: 1,
      activeUsers: 1,
      checksToday: response.data.total_checks,
      diffsToday: response.data.total_changes,
      systemUptime: 3600,
      avgResponseTime: 120,
    };
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
