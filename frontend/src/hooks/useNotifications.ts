import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsApi } from '../lib/api';
import type { CreateNotificationRuleRequest, UpdateNotificationRuleRequest } from '../types';
import { QUERY_KEYS } from './useAuth';

export function useNotificationsList() {
  return useQuery({
    queryKey: QUERY_KEYS.notifications,
    queryFn: () => notificationsApi.list(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useNotificationById(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.notification(id),
    queryFn: () => notificationsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateNotificationRuleRequest) => notificationsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notifications });
    },
  });
}

export function useUpdateNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateNotificationRuleRequest }) =>
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
