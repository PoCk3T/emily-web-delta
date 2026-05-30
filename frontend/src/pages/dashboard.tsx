import { usePlatformStats } from '../hooks/useAuth';
import { UrlStatusCard } from '../components/urls/UrlStatusCard';
import { getStatusDot } from '../lib/utils';
import { ROUTES } from '../lib/constants';
import { Link } from 'react-router-dom';
import { Globe, Activity, GitCompare, TrendingUp, AlertCircle, Eye, Clock, ArrowUpRight } from 'lucide-react';

export default function DashboardPage() {
  const { data: stats, isLoading } = usePlatformStats();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600" />
          <p className="mt-3 text-sm text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const summaryCards = [
    {
      label: 'Total URLs',
      value: stats?.totalUrls ?? 0,
      icon: Globe,
      color: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-50 dark:bg-blue-900/20',
    },
    {
      label: 'Active Monitors',
      value: stats?.activeUrls ?? 0,
      icon: Activity,
      color: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    },
    {
      label: 'Total Checks',
      value: stats?.totalChecks ?? 0,
      icon: Eye,
      color: 'text-purple-600 dark:text-purple-400',
      bg: 'bg-purple-50 dark:bg-purple-900/20',
    },
    {
      label: 'Total Diffs',
      value: stats?.totalDiffs ?? 0,
      icon: GitCompare,
      color: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-50 dark:bg-amber-900/20',
    },
  ];

  const recentChecks = [
    { id: '1', url: 'openai.com/policies/terms-of-use', status: 'COMPLETED', changed: true, time: '2m ago' },
    { id: '2', url: 'anthropic.com/legal/consumer-terms', status: 'COMPLETED', changed: false, time: '5m ago' },
    { id: '3', url: 'policies.google.com/terms', status: 'FAILED', changed: false, time: '10m ago' },
    { id: '4', url: 'openai.com/policies/privacy-policy', status: 'COMPLETED', changed: true, time: '15m ago' },
    { id: '5', url: 'ai.google.dev/gemini-api/terms', status: 'COMPLETED', changed: false, time: '20m ago' },
  ];

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {summaryCards.map((card) => (
          <div key={card.label} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{card.label}</p>
                <p className="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{card.value}</p>
              </div>
              <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${card.bg}`}>
                <card.icon className={card.color} size={20} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Status Overview */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <UrlStatusCard status="ACTIVE" count={stats?.activeUrls ?? 0} />
        <UrlStatusCard status="ERRORING" count={0} />
        <UrlStatusCard status="DOWN" count={0} />
        <UrlStatusCard status="DELETED" count={0} />
        <UrlStatusCard status="UNREACHABLE" count={0} />
      </div>

      {/* Recent Checks */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Clock size={18} className="text-gray-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Checks</h2>
          </div>
          <Link to={ROUTES.checks} className="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700 dark:text-brand-400">
            View all <ArrowUpRight size={14} />
          </Link>
        </div>
        <div className="divide-y divide-gray-100 dark:divide-gray-700">
          {recentChecks.map((check) => (
            <div key={check.id} className="flex items-center justify-between px-6 py-3">
              <div className="flex items-center gap-3">
                <span className={`inline-block h-2 w-2 rounded-full ${getStatusDot(check.status)}`} />
                <span className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-xs">
                  {check.url}
                </span>
              </div>
              <div className="flex items-center gap-4">
                {check.changed && (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                    <TrendingUp size={12} /> Changed
                  </span>
                )}
                {check.status === 'FAILED' && (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-red-600 dark:text-red-400">
                    <AlertCircle size={12} /> Failed
                  </span>
                )}
                <span className="text-xs text-gray-400">{check.time}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link to={ROUTES.urls} className="btn-primary">
            <Globe size={16} /> Add New URL
          </Link>
          <Link to={`${ROUTES.urls}?tab=firecrawl`} className="btn-secondary">
            Browse Firecrawl Monitors
          </Link>
          <Link to={ROUTES.settings} className="btn-secondary">
            Configure Notifications
          </Link>
        </div>
      </div>
    </div>
  );
}
