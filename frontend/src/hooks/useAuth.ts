import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { LoginCredentials, LoginResponse, ApiError } from '../types';
import { authApi, urlsApi, checksApi, diffsApi, notificationsApi, analyticsApi, usersApi } from '../lib/api';
import { useAuthStore } from '../store/authStore';

export const QUERY_KEYS = {
  urls: ['urls'],
  url: (id: string) => ['url', id],
  checks: ['checks'],
  check: (id: string) => ['check', id],
  diffs: ['diffs'],
  diff: (id: string) => ['diff', id],
  notifications: ['notifications'],
  notification: (id: string) => ['notification', id],
  analytics: (urlId: string) => ['analytics', urlId],
  platformStats: ['platform-stats'],
  users: ['users'],
  currentUser: ['current-user'],
} as const;

export function useLogin() {
  return useMutation<LoginResponse, ApiError, LoginCredentials>({
    mutationFn: (credentials) => authApi.login(credentials),
    onSuccess: (data) => {
      useAuthStore.getState().login(data.token, '');
    },
  });
}

export function useLogout() {
  return useMutation<void, ApiError>({
    mutationFn: () => authApi.logout(),
    onSuccess: () => {
      useAuthStore.getState().logout();
    },
  });
}

export function useCurrentUser() {
  return useQuery({
    queryKey: QUERY_KEYS.currentUser,
    queryFn: () => authApi.me(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useUrls(params?: { page?: number; pageSize?: number; filter?: string }) {
  return useQuery({
    queryKey: [...QUERY_KEYS.urls, params],
    queryFn: () => urlsApi.list(params),
    staleTime: 2 * 60 * 1000,
  });
}

export function useUrl(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.url(id),
    queryFn: () => urlsApi.get(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateUrl() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof urlsApi.create>[0]) => urlsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.urls });
    },
  });
}

export function useUpdateUrl() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof urlsApi.update>[1] }) =>
      urlsApi.update(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.urls });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.url(variables.id) });
    },
  });
}

export function useDeleteUrl() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => urlsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.urls });
    },
  });
}

export function useToggleUrl() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) => urlsApi.toggle(id, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.urls });
    },
  });
}

export function useTriggerCheck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => urlsApi.check(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.checks });
    },
  });
}

export function useChecks(params?: { urlId?: string; page?: number; pageSize?: number }) {
  return useQuery({
    queryKey: [...QUERY_KEYS.checks, params],
    queryFn: () => checksApi.list(params?.urlId, { page: params?.page, pageSize: params?.pageSize }),
    staleTime: 1 * 60 * 1000,
  });
}

export function useCheck(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.check(id),
    queryFn: () => checksApi.get(id),
    enabled: !!id,
  });
}

export function useCreateCheck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof checksApi.create>[0]) => checksApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.checks });
    },
  });
}

export function useDiffs(params?: { urlId?: string; page?: number; pageSize?: number }) {
  return useQuery({
    queryKey: [...QUERY_KEYS.diffs, params],
    queryFn: () => diffsApi.list(params?.urlId, { page: params?.page, pageSize: params?.pageSize }),
    staleTime: 2 * 60 * 1000,
  });
}

export function useDiff(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.diff(id),
    queryFn: () => diffsApi.get(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}

export function useDiffAiSummary(id: string) {
  return useQuery({
    queryKey: [...QUERY_KEYS.diff(id), 'ai-summary'],
    queryFn: () => diffsApi.getAiSummary(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}

export function useNotifications() {
  return useQuery({
    queryKey: QUERY_KEYS.notifications,
    queryFn: () => notificationsApi.list(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof notificationsApi.create>[0]) => notificationsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notifications });
    },
  });
}

export function useUpdateNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof notificationsApi.update>[1] }) =>
      notificationsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notifications });
    },
  });
}

export function useDeleteNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => notificationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notifications });
    },
  });
}

export function useAnalytics(urlId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.analytics(urlId),
    queryFn: () => analyticsApi.get(urlId),
    enabled: !!urlId,
    staleTime: 5 * 60 * 1000,
  });
}

export function usePlatformStats() {
  return useQuery({
    queryKey: QUERY_KEYS.platformStats,
    queryFn: () => analyticsApi.getPlatformStats(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useUsers() {
  return useQuery({
    queryKey: QUERY_KEYS.users,
    queryFn: () => usersApi.list(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpdateUserRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, role }: { id: string; role: Parameters<typeof usersApi.updateRole>[1] }) =>
      usersApi.updateRole(id, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.users });
    },
  });
}
