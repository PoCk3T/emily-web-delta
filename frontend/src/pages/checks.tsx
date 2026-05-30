import { useChecks } from '../hooks/useAuth';
import { formatRelative, getStatusDot } from '../lib/utils';
import { AlertCircle, Activity, Loader2, Search, Filter } from 'lucide-react';
import { useState, useMemo } from 'react';

export default function ChecksPage() {
  const { data: checksData, isLoading } = useChecks();
  const checks = checksData?.items ?? [];
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const filtered = checks.filter((c) => {
    const matchesSearch = !search || c.urlId?.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = !statusFilter || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    checks.forEach((c) => {
      counts[c.status] = (counts[c.status] || 0) + 1;
    });
    return counts;
  }, [checks]);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="Search by URL ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input pl-10"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="select w-36"
          >
            <option value="">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="FAILED">Failed</option>
            <option value="RUNNING">Running</option>
            <option value="PENDING">Pending</option>
          </select>
        </div>
      </div>

      {/* Status Summary */}
      <div className="flex flex-wrap gap-3">
        {Object.entries(statusCounts).map(([status, count]) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status === statusFilter ? '' : status)}
            className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
              statusFilter === status
                ? 'border-brand-300 bg-brand-50 text-brand-700 dark:border-brand-600 dark:bg-brand-900/20 dark:text-brand-400'
                : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'
            }`}
          >
            <span className={`inline-block h-2 w-2 rounded-full ${getStatusDot(status)}`} />
            {status} ({count})
          </button>
        ))}
      </div>

      {/* Checks List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} className="animate-spin text-gray-400" />
          <span className="ml-3 text-sm text-gray-500">Loading checks...</span>
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-12 text-center dark:border-gray-600 dark:bg-gray-800/50">
          <Activity size={40} className="mx-auto mb-4 text-gray-400" />
          <h3 className="mb-1 text-lg font-medium text-gray-900 dark:text-white">
            {search || statusFilter ? 'No checks found' : 'No checks yet'}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {search || statusFilter ? 'Try adjusting your filters' : 'Checks will appear here as URLs are monitored'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((check) => (
            <div key={check.id} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`inline-block h-2 w-2 rounded-full ${getStatusDot(check.status)}`} />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Check #{check.id}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      URL ID: {check.urlId || 'N/A'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {check.statusCode && (
                    <span className="text-xs font-mono text-gray-500 dark:text-gray-400">
                      HTTP {check.statusCode}
                    </span>
                  )}
                  {check.loadTime != null && (
                    <span className="text-xs text-gray-400">{check.loadTime}ms</span>
                  )}
                  <span className="text-xs text-gray-400">{formatRelative(check.completedAt)}</span>
                </div>
              </div>
              {check.error && (
                <div className="mt-2 flex items-center gap-1 text-xs text-red-600 dark:text-red-400">
                  <AlertCircle size={12} />
                  {check.error}
                </div>
              )}
              {check.contentLength != null && (
                <div className="mt-1 text-xs text-gray-400">
                  Content: {check.contentLength} bytes
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {checksData && checksData.totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Page {checksData.page} of {checksData.totalPages}
          </span>
        </div>
      )}
    </div>
  );
}
