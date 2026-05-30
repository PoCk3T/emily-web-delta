import React, { useState } from 'react';
import { X } from 'lucide-react';
import type { CreateUrlRequest, Backend } from '../../types';

interface UrlFormProps {
  onSubmit: (data: CreateUrlRequest) => void;
  onCancel: () => void;
  initialData?: Partial<CreateUrlRequest>;
  isSubmitting?: boolean;
}

export function UrlForm({ onSubmit, onCancel, initialData, isSubmitting = false }: UrlFormProps) {
  const [url, setUrl] = useState(initialData?.url || '');
  const [name, setName] = useState(initialData?.name || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [backend, setBackend] = useState<Backend>(initialData?.backend || 'firecrawl');
  const [checkInterval, setCheckInterval] = useState(initialData?.checkInterval || 30);
  const [tags, setTags] = useState(initialData?.tags?.join(', ') || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      url,
      name,
      description: description || undefined,
      backend,
      checkInterval,
      tags: tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {initialData?.url ? 'Edit URL' : 'Add New URL'}
        </h3>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
        >
          <X size={18} />
        </button>
      </div>

      <div>
        <label htmlFor="url" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          URL
        </label>
        <input
          id="url"
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          className="mt-1 input"
        />
      </div>

      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Name
        </label>
        <input
          id="name"
          type="text"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My Website"
          className="mt-1 input"
        />
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Optional description..."
          rows={2}
          className="mt-1 input resize-none"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="backend" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Backend
          </label>
          <select
            id="backend"
            value={backend}
            onChange={(e) => setBackend(e.target.value as Backend)}
            className="mt-1 select"
          >
            <option value="firecrawl">Firecrawl</option>
            <option value="selfhosted">Self-hosted</option>
          </select>
        </div>

        <div>
          <label htmlFor="interval" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Check Interval (minutes)
          </label>
          <input
            id="interval"
            type="number"
            min={5}
            max={1440}
            value={checkInterval}
            onChange={(e) => setCheckInterval(Number(e.target.value))}
            className="mt-1 input"
          />
        </div>
      </div>

      <div>
        <label htmlFor="tags" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Tags (comma-separated)
        </label>
        <input
          id="tags"
          type="text"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="important, personal"
          className="mt-1 input"
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <button type="button" onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
        <button type="submit" disabled={isSubmitting} className="btn-primary">
          {isSubmitting ? 'Saving...' : initialData?.url ? 'Update URL' : 'Add URL'}
        </button>
      </div>
    </form>
  );
}
