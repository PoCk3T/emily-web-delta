import React from 'react';
import { Link } from 'react-router-dom';
import { ExternalLink, Globe, Clock, Tag, MoreVertical, Play, Trash2, Edit, Eye } from 'lucide-react';
import type { Url, Status } from '../../types';
import { formatDate, formatRelative, getStatusColor, getStatusDot } from '../../lib/utils';
import { ROUTES } from '../../lib/constants';

interface UrlCardProps {
  url: Url;
  onToggle?: (id: string, enabled: boolean) => void;
  onDelete?: (id: string) => void;
  onCheck?: (id: string) => void;
  onEdit?: (url: Url) => void;
}

const backendLabels: Record<string, string> = {
  firecrawl: 'Firecrawl',
  selfhosted: 'Self-hosted',
};

export function UrlCard({ url, onToggle, onDelete, onCheck, onEdit }: UrlCardProps) {
  const [menuOpen, setMenuOpen] = React.useState(false);

  return (
    <div className="group relative rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-all hover:border-gray-300 hover:shadow-md dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <Link
            to={ROUTES.urlDetail.replace(':id', url.id)}
            className="flex items-center gap-2 text-lg font-semibold text-gray-900 hover:text-brand-600 dark:text-white dark:hover:text-brand-400"
          >
            <Globe size={18} className="shrink-0 text-gray-400" />
            <span className="truncate">{url.name}</span>
          </Link>
          <a
            href={url.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-brand-600 dark:text-gray-400 dark:hover:text-brand-400"
          >
            <span className="truncate">{url.url}</span>
            <ExternalLink size={12} />
          </a>
        </div>

        <div className="relative ml-4 shrink-0">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="rounded-md p-1 text-gray-400 opacity-0 transition-opacity hover:bg-gray-100 hover:text-gray-600 group-hover:opacity-100 dark:hover:bg-gray-700 dark:hover:text-gray-300"
          >
            <MoreVertical size={16} />
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-full z-10 mt-1 w-40 rounded-lg border border-gray-200 bg-white py-1 shadow-lg dark:border-gray-700 dark:bg-gray-800">
              <Link
                to={ROUTES.urlDetail.replace(':id', url.id)}
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700"
                onClick={() => setMenuOpen(false)}
              >
                <Eye size={14} /> View
              </Link>
              <button
                onClick={() => { onEdit?.(url); setMenuOpen(false); }}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                <Edit size={14} /> Edit
              </button>
              <button
                onClick={() => { onCheck?.(url.id); setMenuOpen(false); }}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                <Play size={14} /> Check Now
              </button>
              <hr className="my-1 border-gray-100 dark:border-gray-700" />
              <button
                onClick={() => { onDelete?.(url.id); setMenuOpen(false); }}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
              >
                <Trash2 size={14} /> Delete
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
        <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusColor(url.status)}`}>
          <span className={`inline-block h-1.5 w-1.5 rounded-full ${getStatusDot(url.status)}`} />
          {url.status}
        </span>
        <span className="inline-flex items-center gap-1">
          <Clock size={14} />
          {formatRelative(url.lastCheckedAt)}
        </span>
        <span className="inline-flex items-center gap-1">
          <Globe size={14} />
          {backendLabels[url.backend] || url.backend}
        </span>
        {url.tags.length > 0 && (
          <span className="inline-flex items-center gap-1">
            <Tag size={14} />
            {url.tags.slice(0, 3).join(', ')}
            {url.tags.length > 3 && ` +${url.tags.length - 3}`}
          </span>
        )}
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
          url.enabled
            ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
            : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
        }`}>
          {url.enabled ? 'Enabled' : 'Disabled'}
        </span>
        <span className="text-xs text-gray-400 dark:text-gray-500">
          Every {url.checkInterval}m
        </span>
      </div>
    </div>
  );
}
