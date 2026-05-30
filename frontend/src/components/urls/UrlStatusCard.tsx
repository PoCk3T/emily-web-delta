import React from 'react';
import type { Status } from '../../types';

interface UrlStatusCardProps {
  status: Status;
  label?: string;
  count?: number;
  onClick?: () => void;
  className?: string;
}

const statusConfig: Record<Status, { bg: string; text: string; dot: string; label: string }> = {
  ACTIVE: {
    bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    text: 'text-emerald-700 dark:text-emerald-400',
    dot: 'bg-emerald-500',
    label: 'Active',
  },
  ERRORING: {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    text: 'text-amber-700 dark:text-amber-400',
    dot: 'bg-amber-500',
    label: 'Erroring',
  },
  DOWN: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    text: 'text-red-700 dark:text-red-400',
    dot: 'bg-red-500',
    label: 'Down',
  },
  DELETED: {
    bg: 'bg-orange-50 dark:bg-orange-900/20',
    text: 'text-orange-700 dark:text-orange-400',
    dot: 'bg-orange-500',
    label: 'Deleted',
  },
  UNREACHABLE: {
    bg: 'bg-fuchsia-50 dark:bg-fuchsia-900/20',
    text: 'text-fuchsia-700 dark:text-fuchsia-400',
    dot: 'bg-fuchsia-500',
    label: 'Unreachable',
  },
};

export function UrlStatusCard({ status, label, count, onClick, className = '' }: UrlStatusCardProps) {
  const config = statusConfig[status];

  return (
    <button
      onClick={onClick}
      className={`flex items-center justify-between rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition-all hover:shadow-md dark:border-gray-700 dark:bg-gray-800 ${
        onClick ? 'cursor-pointer hover:border-brand-300 dark:hover:border-brand-600' : ''
      } ${className}`}
    >
      <div className="flex items-center gap-3">
        <span className={`inline-block h-3 w-3 rounded-full ${config.dot}`} />
        <span className={`text-sm font-medium ${config.text}`}>
          {label || config.label}
        </span>
      </div>
      <span className="text-2xl font-bold text-gray-900 dark:text-white">
        {count ?? 0}
      </span>
    </button>
  );
}
