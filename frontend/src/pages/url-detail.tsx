import { useParams, Link } from 'react-router-dom';
import { useUrl, useChecks, useDiffs, useTriggerCheck } from '../hooks/useAuth';
import { getStatusColor, getStatusDot, formatRelative } from '../lib/utils';
import { ROUTES } from '../lib/constants';
import { ArrowLeft, RefreshCw, Globe, Clock, Tag, ExternalLink, GitCompare, Activity, AlertCircle } from 'lucide-react';

export default function UrlDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: url, isLoading } = useUrl(id ?? '');
  const { data: checksData } = useChecks({ urlId: id });
  const { data: diffsData } = useDiffs({ urlId: id });
  const checkMutation = useTriggerCheck();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600" />
          <p className="mt-3 text-sm text-gray-500">Loading URL details...</p>
        </div>
      </div>
    );
  }

  if (!url) {
    return (
      <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-12 text-center dark:border-gray-600 dark:bg-gray-800/50">
        <AlertCircle size={40} className="mx-auto mb-4 text-gray-400" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">URL not found</h3>
        <Link to={ROUTES.urls} className="mt-4 btn-primary">
          Back to URLs
        </Link>
      </div>
    );
  }

  const checks = checksData?.items ?? [];
  const diffs = diffsData?.items ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to={ROUTES.urls} className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300">
          <ArrowLeft size={20} />
        </Link>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">{url.name}</h1>
          <a
            href={url.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700 dark:text-brand-400"
          >
            <span className="truncate">{url.url}</span>
            <ExternalLink size={12} />
          </a>
        </div>
        <button
          onClick={() => checkMutation.mutate(url.id)}
          disabled={checkMutation.isPending}
          className="btn-primary"
        >
          <RefreshCw size={16} className={checkMutation.isPending ? 'animate-spin' : ''} />
          Check Now
        </button>
      </div>

      {/* URL Info */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <Globe size={16} />
            <span>Status</span>
          </div>
          <span className={`mt-1 inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-sm font-medium ${getStatusColor(url.status)}`}>
            <span className={`inline-block h-2 w-2 rounded-full ${getStatusDot(url.status)}`} />
            {url.status}
          </span>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <Clock size={16} />
            <span>Last Checked</span>
          </div>
          <p className="mt-1 text-sm font-medium text-gray-900 dark:text-white">
            {url.lastCheckedAt ? formatRelative(url.lastCheckedAt) : 'Never'}
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <Activity size={16} />
            <span>Interval</span>
          </div>
          <p className="mt-1 text-sm font-medium text-gray-900 dark:text-white">Every {url.checkInterval}m</p>
        </div>
      </div>

      {/* Tags */}
      {url.tags.length > 0 && (
        <div className="flex items-center gap-2">
          <Tag size={16} className="text-gray-400" />
          {url.tags.map((tag) => (
            <span key={tag} className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-300">
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Checks Timeline */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-center gap-2 border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <Activity size={18} className="text-gray-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Checks</h2>
        </div>
        {checks.length === 0 ? (
          <div className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">No checks yet</div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {checks.slice(0, 10).map((check) => (
              <div key={check.id} className="flex items-center justify-between px-6 py-3">
                <div className="flex items-center gap-3">
                  <span className={`inline-block h-2 w-2 rounded-full ${getStatusDot(check.status)}`} />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{check.status}</span>
                  {check.error && (
                    <span className="text-xs text-red-500">{check.error}</span>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  {check.loadTime != null && (
                    <span className="text-xs text-gray-400">{check.loadTime}ms</span>
                  )}
                  <span className="text-xs text-gray-400">{formatRelative(check.completedAt)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Diffs */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <GitCompare size={18} className="text-gray-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Diffs</h2>
          </div>
          <Link to={`${ROUTES.diffs}?urlId=${url.id}`} className="text-sm text-brand-600 hover:text-brand-700 dark:text-brand-400">
            View all diffs
          </Link>
        </div>
        {diffs.length === 0 ? (
          <div className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">No diffs yet</div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {diffs.slice(0, 5).map((diff) => (
              <div key={diff.id} className="flex items-center justify-between px-6 py-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-gray-700 dark:text-gray-300">
                    {diff.summary || 'No summary available'}
                  </p>
                  <p className="text-xs text-gray-400">{diff.diffType} • {formatRelative(diff.createdAt)}</p>
                </div>
                <Link to={`${ROUTES.diffs}/${diff.id}`} className="ml-4 text-sm text-brand-600 hover:text-brand-700 dark:text-brand-400">
                  View
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
