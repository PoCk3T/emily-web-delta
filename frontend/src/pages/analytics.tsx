import React from 'react';
import { useAnalytics, useUrl } from '../hooks/useAuth';
import { useParams } from 'react-router-dom';
import { TrendingUp, TrendingDown, Minus, AlertTriangle, BarChart3, Activity } from 'lucide-react';

export default function AnalyticsPage() {
  const { id } = useParams<{ id: string }>();
  const { data: analytics, isLoading } = useAnalytics(id ?? '');
  const { data: url } = useUrl(id ?? '');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600" />
          <p className="mt-3 text-sm text-gray-500">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-12 text-center dark:border-gray-600 dark:bg-gray-800/50">
        <BarChart3 size={40} className="mx-auto mb-4 text-gray-400" />
        <h3 className="mb-1 text-lg font-medium text-gray-900 dark:text-white">No analytics data</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Analytics will appear after checks are performed
        </p>
      </div>
    );
  }

  const trendIcons = {
    increasing: <TrendingUp size={16} className="text-red-500" />,
    decreasing: <TrendingDown size={16} className="text-emerald-500" />,
    stable: <Minus size={16} className="text-gray-400" />,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          {url?.name ? `Analytics for ${url.name}` : 'URL Analytics'}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Change frequency, trends, and anomaly detection
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Checks</p>
          <p className="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{analytics.totalChecks}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Diffs</p>
          <p className="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{analytics.totalDiffs}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Avg Load Time</p>
          <p className="mt-1 text-3xl font-bold text-gray-900 dark:text-white">
            {analytics.averageLoadTime != null ? `${Math.round(analytics.averageLoadTime)}ms` : '—'}
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Uptime</p>
          <p className="mt-1 text-3xl font-bold text-gray-900 dark:text-white">
            {analytics.uptimePercentage != null ? `${analytics.uptimePercentage}%` : '—'}
          </p>
        </div>
      </div>

      {/* Trend */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
          <Activity size={20} /> Change Trend
        </h2>
        {analytics.trend && (
          <div className="flex items-center gap-4">
            {trendIcons[analytics.trend.direction] || <Minus size={16} className="text-gray-400" />}
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                {analytics.trend.direction}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Rate: {analytics.trend.rate} • Confidence: {Math.round(analytics.trend.confidence * 100)}%
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Change Frequency Chart (placeholder) */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Change Frequency</h2>
        {analytics.changeFrequency.length === 0 ? (
          <div className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">No frequency data yet</div>
        ) : (
          <div className="chart-container flex items-end gap-1">
            {analytics.changeFrequency.slice(-30).map((entry, i) => {
              const maxChanges = Math.max(...analytics.changeFrequency.map((f) => f.changes), 1);
              const height = maxChanges > 0 ? (entry.changes / maxChanges) * 100 : 0;
              return (
                <div key={i} className="flex flex-1 flex-col items-center gap-1">
                  <div
                    className="w-full rounded-t bg-brand-500 transition-all hover:bg-brand-600 dark:bg-brand-400 dark:hover:bg-brand-500"
                    style={{ height: `${Math.max(height, 4)}%` }}
                    title={`${entry.date}: ${entry.changes} changes`}
                  />
                  {i % 5 === 0 && (
                    <span className="text-[10px] text-gray-400">{entry.date}</span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Anomalies */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Anomalies</h2>
        </div>
        {analytics.anomalies.length === 0 ? (
          <div className="px-6 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
            No anomalies detected
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {analytics.anomalies.map((anomaly, i) => (
              <div key={i} className="flex items-center justify-between px-6 py-3">
                <div className="flex items-center gap-3">
                  <AlertTriangle size={16} className="text-amber-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                      {anomaly.type.replace('_', ' ')}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{anomaly.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-medium ${
                    anomaly.severity === 'high' ? 'text-red-600 dark:text-red-400' :
                    anomaly.severity === 'medium' ? 'text-amber-600 dark:text-amber-400' :
                    'text-blue-600 dark:text-blue-400'
                  }`}>
                    {anomaly.severity}
                  </span>
                  <span className="text-xs text-gray-400">{anomaly.date}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
