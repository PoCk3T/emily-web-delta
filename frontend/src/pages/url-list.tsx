import React from 'react';
import { useUrls, useCreateUrl, useUpdateUrl, useDeleteUrl, useToggleUrl, useTriggerCheck } from '../hooks/useAuth';
import { UrlList } from '../components/urls/UrlList';
import type { CreateUrlRequest } from '../types';

export default function UrlListPage() {
  const { data: urlsData, isLoading, error } = useUrls();
  const createMutation = useCreateUrl();
  const updateMutation = useUpdateUrl();
  const deleteMutation = useDeleteUrl();
  const toggleMutation = useToggleUrl();
  const checkMutation = useTriggerCheck();

  const urls = urlsData?.items ?? [];

  const handleCreate = (data: CreateUrlRequest) => {
    createMutation.mutate(data);
  };

  const handleUpdate = (id: string, data: Partial<CreateUrlRequest>) => {
    updateMutation.mutate({ id, data });
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id);
  };

  const handleToggle = (id: string, enabled: boolean) => {
    toggleMutation.mutate({ id, enabled });
  };

  const handleCheck = (id: string) => {
    checkMutation.mutate(id);
  };

  return (
    <UrlList
      urls={urls}
      isLoading={isLoading}
      error={error?.message ?? null}
      onCreate={handleCreate}
      onUpdate={handleUpdate}
      onDelete={handleDelete}
      onToggle={handleToggle}
      onCheck={handleCheck}
    />
  );
}
