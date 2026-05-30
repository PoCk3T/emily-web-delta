import { useDiffs, useDiffAiSummary } from '../hooks/useAuth';
import { formatRelative } from '../lib/utils';
import { GitCompare, Loader2, Sparkles } from 'lucide-react';
import { useState } from 'react';

export default function DiffsPage() {
  const { data: diffsData, isLoading } = useDiffs();
  const diffs = diffsData?.items ?? [];

  const [selectedDiffId, setSelectedDiffId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'unified' | 'side-by-side' | 'json'>('unified');

  const selectedDiff = diffs.find((d) => d.id === selectedDiffId) ?? null;
  const { data: aiSummaryData } = useDiffAiSummary(selectedDiffId ?? '');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 size={24} className="animate-spin text-gray-400" />
        <span className="ml-3 text-sm text-gray-500">Loading diffs...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* View Mode Tabs */}
      <div className="flex items-center gap-1 rounded-lg border border-gray-200 p-1 dark:border-gray-700">
        {(['unified', 'side-by-side', 'json'] as const).map((mode) => (
          <button
            key={mode}
            onClick={() => setViewMode(mode)}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              viewMode === mode
                ? 'bg-brand-600 text-white'
                : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
            }`}
          >
            {mode === 'unified' ? 'Unified' : mode === 'side-by-side' ? 'Side-by-Side' : 'JSON'}
          </button>
        ))}
      </div>

      {/* Diff List */}
      {diffs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-12 text-center dark:border-gray-600 dark:bg-gray-800/50">
          <GitCompare size={40} className="mx-auto mb-4 text-gray-400" />
          <h3 className="mb-1 text-lg font-medium text-gray-900 dark:text-white">No diffs yet</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Diffs will appear here when URL content changes
          </p>
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          {/* List */}
          <div className="lg:col-span-1">
            <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="border-b border-gray-200 px-4 py-3 dark:border-gray-700">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white">All Diffs</h3>
              </div>
              <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto dark:divide-gray-700">
                {diffs.map((diff) => (
                  <button
                    key={diff.id}
                    onClick={() => setSelectedDiffId(diff.id)}
                    className={`w-full px-4 py-3 text-left transition-colors ${
                      selectedDiffId === diff.id
                        ? 'bg-brand-50 dark:bg-brand-900/20'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <p className="truncate text-sm font-medium text-gray-900 dark:text-white">
                        Diff #{diff.id}
                      </p>
                      <span className="text-xs text-gray-400">{formatRelative(diff.createdAt)}</span>
                    </div>
                    <p className="mt-1 truncate text-xs text-gray-500 dark:text-gray-400">
                      {diff.diffType} • URL: {diff.urlId}
                    </p>
                    {diff.summary && (
                      <p className="mt-1 truncate text-xs text-gray-400 dark:text-gray-500">{diff.summary}</p>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Detail */}
          <div className="lg:col-span-2">
            {selectedDiff ? (
              <div className="space-y-4">
                {/* AI Summary */}
                {(aiSummaryData?.summary || selectedDiff.aiSummary) && (
                  <div className="rounded-lg border border-brand-200 bg-brand-50 p-4 dark:border-brand-800 dark:bg-brand-900/20">
                    <div className="flex items-center gap-2 text-sm font-semibold text-brand-700 dark:text-brand-300">
                      <Sparkles size={16} /> AI Summary
                    </div>
                    <p className="mt-1 text-sm text-brand-600 dark:text-brand-400">
                      {aiSummaryData?.summary || selectedDiff.aiSummary}
                    </p>
                  </div>
                )}

                {/* Diff Content */}
                <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
                  <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                      {selectedDiff.diffType === 'json' ? 'JSON Diff' : selectedDiff.diffType === 'html' ? 'HTML Diff' : 'Text Diff'}
                    </h3>
                    <span className="text-xs text-gray-400">
                      {formatRelative(selectedDiff.createdAt)}
                    </span>
                  </div>
                  <div className="overflow-x-auto p-4">
                    <pre className="whitespace-pre-wrap text-xs font-mono text-gray-700 dark:text-gray-300">
                      {selectedDiff.diffContent || '(No diff content)'}
                    </pre>
                  </div>
                </div>

                {/* Checksums */}
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Previous Checksum</p>
                    <p className="mt-1 truncate font-mono text-xs text-gray-700 dark:text-gray-300">
                      {selectedDiff.previousChecksum || 'N/A'}
                    </p>
                  </div>
                  <div className="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Current Checksum</p>
                    <p className="mt-1 truncate font-mono text-xs text-gray-700 dark:text-gray-300">
                      {selectedDiff.currentChecksum || 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 p-12 dark:border-gray-600 dark:bg-gray-800/50">
                <div className="text-center">
                  <GitCompare size={40} className="mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">Select a diff</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Choose a diff from the list to view details</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
