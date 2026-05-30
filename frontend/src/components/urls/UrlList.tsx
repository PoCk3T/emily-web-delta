import React, { useState } from 'react';
import { UrlCard } from './UrlCard';
import { UrlForm } from './UrlForm';
import type { Url, CreateUrlRequest } from '../../types';
import { Plus, Search, Loader2, AlertCircle } from 'lucide-react';

interface UrlListProps {
  urls: Url[];
  isLoading: boolean;
  error: string | null;
  onCreate: (data: CreateUrlRequest) => void;
  onUpdate: (id: string, data: Partial<Url>) => void;
  onDelete: (id: string) => void;
  onToggle: (id: string, enabled: boolean) => void;
  onCheck: (id: string) => void;
}

export function UrlList({ urls, isLoading, error, onCreate, onUpdate, onDelete, onToggle, onCheck }: UrlListProps) {
  const [showForm, setShowForm] = useState(false);
  const [editingUrl, setEditingUrl] = useState<Url | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredUrls = urls.filter(
    (url) =>
      url.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      url.url.toLowerCase().includes(searchQuery.toLowerCase()) ||
      url.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase())),
  );

  const handleEdit = (url: Url) => {
    setEditingUrl(url);
    setShowForm(true);
  };

  return (
    <div>
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="Search URLs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input pl-10"
          />
        </div>
        <button onClick={() => { setEditingUrl(null); setShowForm(true); }} className="btn-primary">
          <Plus size={16} />
          Add URL
        </button>
      </div>

      {showForm && (
        <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <UrlForm
            onSubmit={(data) => {
              if (editingUrl) {
                onUpdate(editingUrl.id, data);
              } else {
                onCreate(data);
              }
              setShowForm(false);
              setEditingUrl(null);
            }}
            onCancel={() => { setShowForm(false); setEditingUrl(null); }}
            initialData={editingUrl || undefined}
          />
        </div>
      )}

      {error && (
        <div className="mb-6 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} className="animate-spin text-gray-400" />
          <span className="ml-3 text-sm text-gray-500">Loading URLs...</span>
        </div>
      ) : filteredUrls.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-12 text-center dark:border-gray-600 dark:bg-gray-800/50">
          <Globe size={40} className="mx-auto mb-4 text-gray-400" />
          <h3 className="mb-1 text-lg font-medium text-gray-900 dark:text-white">
            {searchQuery ? 'No URLs found' : 'No URLs added yet'}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {searchQuery
              ? 'Try a different search term'
              : 'Get started by adding your first URL to monitor'}
          </p>
          {!searchQuery && (
            <button onClick={() => setShowForm(true)} className="mt-4 btn-primary">
              <Plus size={16} />
              Add Your First URL
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredUrls.map((url) => (
            <UrlCard
              key={url.id}
              url={url}
              onToggle={onToggle}
              onDelete={onDelete}
              onCheck={onCheck}
              onEdit={handleEdit}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function Globe({ size, className }: { size: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
      <path d="M2 12h20" />
    </svg>
  );
}
