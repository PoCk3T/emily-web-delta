import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { urlsApi, checksApi, diffsApi } from '../lib/api';
import type { CreateUrlRequest, UpdateUrlRequest, CreateCheckRequest } from '../types';
import { QUERY_KEYS } from './useAuth';

export function useUrlsList(params?: { page?: number; pageSize?: number; filter?: string }) {
  return useQuery({
    queryKey: [...QUERY_KEYS.urls, params],
    queryFn: () => urlsApi.list(params),
    staleTime: 2 * 60 * 1000,
  });
}

export function useUrlById(id: string) {
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
    mutationFn: (data: CreateUrlRequest) => urlsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.urls });
    },
  });
}

export function useUpdateUrl() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateUrlRequest }) => urlsApi.update(id, data),
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

export function useChecksList(params?: { urlId?: string; page?: number; pageSize?: number }) {
  return useQuery({
    queryKey: [...QUERY_KEYS.checks, params],
    queryFn: () => checksApi.list(params?.urlId, { page: params?.page, pageSize: params?.pageSize }),
    staleTime: 1 * 60 * 1000,
  });
}

export function useCheckById(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.check(id),
    queryFn: () => checksApi.get(id),
    enabled: !!id,
  });
}

export function useCreateCheck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateCheckRequest) => checksApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.checks });
    },
  });
}

export function useDiffsList(params?: { urlId?: string; page?: number; pageSize?: number }) {
  return useQuery({
    queryKey: [...QUERY_KEYS.diffs, params],
    queryFn: () => diffsApi.list(params?.urlId, { page: params?.page, pageSize: params?.pageSize }),
    staleTime: 2 * 60 * 1000,
  });
}

export function useDiffById(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.diff(id),
    queryFn: () => diffsApi.get(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}
