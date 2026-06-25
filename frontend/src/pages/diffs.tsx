import { useDiffs, useDiffAiSummary, useUrls } from '../hooks/useAuth';
import { formatRelative } from '../lib/utils';
import { GitCompare, Loader2, Sparkles, ExternalLink } from 'lucide-react';
import { useState } from 'react';

// Unified Diff Row Extractor
function parseUnifiedDiff(diffText: string) {
  if (!diffText) return [];
  const lines = diffText.split('\n');
  return lines.map((line, idx) => {
    let type: 'addition' | 'deletion' | 'info' | 'normal' = 'normal';
    if (line.startsWith('+') && !line.startsWith('+++')) {
      type = 'addition';
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      type = 'deletion';
    } else if (line.startsWith('@@')) {
      type = 'info';
    }
    return { id: idx, line, type };
  });
}

// Side-by-Side Diff Line Extractor
function parseSideBySideDiff(diffText: string) {
  if (!diffText) return [];
  const lines = diffText.split('\n');
  const rows: Array<{
    id: number;
    left: { line: string; type: 'deletion' | 'normal' | 'empty' };
    right: { line: string; type: 'addition' | 'normal' | 'empty' };
  }> = [];

  let lineIdx = 0;
  while (lineIdx < lines.length) {
    const line = lines[lineIdx];

    if (line.startsWith('---') || line.startsWith('+++') || line.startsWith('@@')) {
      rows.push({
        id: lineIdx,
        left: { line, type: 'normal' },
        right: { line, type: 'normal' }
      });
      lineIdx++;
    } else if (line.startsWith('-')) {
      // Deletion on left. Check if next line is an addition on right
      let rightLine = '';
      let rightType: 'addition' | 'empty' = 'empty';
      if (lineIdx + 1 < lines.length && lines[lineIdx + 1].startsWith('+')) {
        rightLine = lines[lineIdx + 1].substring(1);
        rightType = 'addition';
        lineIdx += 2;
      } else {
        lineIdx++;
      }
      rows.push({
        id: lineIdx,
        left: { line: line.substring(1), type: 'deletion' },
        right: { line: rightLine, type: rightType }
      });
    } else if (line.startsWith('+')) {
      // Addition on right (no deletion on left)
      rows.push({
        id: lineIdx,
        left: { line: '', type: 'empty' },
        right: { line: line.substring(1), type: 'addition' }
      });
      lineIdx++;
    } else {
      // Normal line
      const cleanLine = line.startsWith(' ') ? line.substring(1) : line;
      rows.push({
        id: lineIdx,
        left: { line: cleanLine, type: 'normal' },
        right: { line: cleanLine, type: 'normal' }
      });
      lineIdx++;
    }
  }
  return rows;
}

function UnifiedDiffViewer({ diffContent }: { diffContent: string }) {
  const parsed = parseUnifiedDiff(diffContent);
  return (
    <div className="font-mono text-xs divide-y divide-gray-100 dark:divide-gray-800 bg-gray-50 dark:bg-gray-900 rounded-lg p-3 overflow-x-auto max-h-[500px]">
      {parsed.map((row) => {
        let rowClass = "text-gray-700 dark:text-gray-300 px-2 py-0.5";
        if (row.type === 'addition') {
          rowClass = "bg-green-50 text-green-700 dark:bg-green-950/30 dark:text-green-400 px-2 py-0.5";
        } else if (row.type === 'deletion') {
          rowClass = "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400 px-2 py-0.5";
        } else if (row.type === 'info') {
          rowClass = "bg-blue-50/50 text-blue-600 dark:bg-blue-950/20 dark:text-blue-400 font-semibold px-2 py-1 border-y border-blue-100 dark:border-blue-900/30";
        }
        return (
          <div key={row.id} className={rowClass}>
            {row.line}
          </div>
        );
      })}
    </div>
  );
}

function SideBySideDiffViewer({ diffContent }: { diffContent: string }) {
  const rows = parseSideBySideDiff(diffContent);
  return (
    <div className="font-mono text-xs divide-y divide-gray-100 dark:divide-gray-800 bg-gray-50 dark:bg-gray-900 rounded-lg overflow-x-auto max-h-[500px] border border-gray-200 dark:border-gray-700">
      <div className="grid grid-cols-2 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 font-semibold px-4 py-2 text-gray-600 dark:text-gray-300 text-center">
        <div>Previous Content</div>
        <div className="border-l border-gray-200 dark:border-gray-700">Current Content</div>
      </div>
      {rows.map((row) => {
        let leftClass = "px-3 py-1 truncate";
        let rightClass = "px-3 py-1 truncate border-l border-gray-200 dark:border-gray-700";

        if (row.left.type === 'deletion') {
          leftClass += " bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400";
        } else if (row.left.type === 'empty') {
          leftClass += " bg-gray-100/50 dark:bg-gray-800/20 text-transparent select-none";
        }

        if (row.right.type === 'addition') {
          rightClass += " bg-green-50 text-green-700 dark:bg-green-950/30 dark:text-green-400";
        } else if (row.right.type === 'empty') {
          rightClass += " bg-gray-100/50 dark:bg-gray-800/20 text-transparent select-none";
        }

        return (
          <div key={row.id} className="grid grid-cols-2">
            <div className={leftClass}>{row.left.line || ' '}</div>
            <div className={rightClass}>{row.right.line || ' '}</div>
          </div>
        );
      })}
    </div>
  );
}

function JsonDiffViewer({ selectedDiff }: { selectedDiff: any }) {
  const jsonStr = JSON.stringify(selectedDiff, null, 2);
  return (
    <div className="font-mono text-xs bg-gray-50 dark:bg-gray-900 rounded-lg p-4 overflow-x-auto max-h-[500px] text-gray-700 dark:text-gray-300">
      <pre>{jsonStr}</pre>
    </div>
  );
}

export default function DiffsPage() {
  const { data: diffsData, isLoading } = useDiffs();
  const diffs = diffsData?.items ?? [];

  const { data: urlsData } = useUrls({ pageSize: 1000 });
  const urls = urlsData?.items ?? [];

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
      <div className="flex items-center gap-1 rounded-lg border border-gray-200 p-1 dark:border-gray-700 bg-white dark:bg-gray-800">
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
                {diffs.map((diff) => {
                  const urlObj = urls.find((u) => u.id === diff.urlId);
                  return (
                  <button
                    key={diff.id}
                    onClick={() => {
                      setSelectedDiffId(diff.id);
                    }}
                    className={`w-full px-4 py-3 text-left transition-colors ${
                      selectedDiffId === diff.id
                        ? 'bg-brand-50 dark:bg-brand-900/20'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <p className="truncate text-sm font-medium text-gray-900 dark:text-white">
                        Diff #{diff.id.substring(0, 8)}
                      </p>
                      <span className="text-xs text-gray-400">{formatRelative(diff.createdAt)}</span>
                    </div>
                    <p className="mt-1 truncate text-xs text-gray-500 dark:text-gray-400">
                      {diff.diffType} • URL: {urlObj?.name || diff.urlId.substring(0, 8)}
                    </p>
                    {urlObj && (
                      <div className="mt-1 flex items-center gap-1 text-xs text-brand-600 dark:text-brand-400 hover:underline">
                        <ExternalLink size={12} />
                        <a href={urlObj.url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} className="truncate">
                          {urlObj.url}
                        </a>
                      </div>
                    )}
                    {diff.summary && (
                      <p className="mt-1 truncate text-xs text-gray-400 dark:text-gray-500">{diff.summary}</p>
                    )}
                  </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Detail */}
          <div className="lg:col-span-2">
            {selectedDiff ? (
              <div className="space-y-4">
                {/* Selected URL Context */}
                {(() => {
                  const urlObj = urls.find((u) => u.id === selectedDiff.urlId);
                  if (!urlObj) return null;
                  return (
                    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {urlObj.name}
                      </h2>
                      <div className="mt-1 flex items-center gap-1 text-sm text-brand-600 dark:text-brand-400 hover:underline">
                        <ExternalLink size={14} />
                        <a href={urlObj.url} target="_blank" rel="noopener noreferrer" className="truncate">
                          {urlObj.url}
                        </a>
                      </div>
                    </div>
                  );
                })()}

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

                {/* Diff Content Tab Routing */}
                <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800 p-4">
                  {viewMode === 'unified' && (
                    <UnifiedDiffViewer diffContent={selectedDiff.diffContent} />
                  )}
                  {viewMode === 'side-by-side' && (
                    <SideBySideDiffViewer diffContent={selectedDiff.diffContent} />
                  )}
                  {viewMode === 'json' && (
                    <JsonDiffViewer selectedDiff={selectedDiff} />
                  )}
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
