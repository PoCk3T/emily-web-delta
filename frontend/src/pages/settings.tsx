import React from 'react';
import { useNotifications, useCreateNotification, useUpdateNotification, useDeleteNotification } from '../hooks/useAuth';
import { formatDate } from '../lib/utils';
import { Bell, Plus, Trash2, Edit, Loader2, AlertCircle } from 'lucide-react';
import { NOTIFICATION_CHANNELS, NOTIFICATION_FREQUENCIES } from '../lib/constants';
import type { CreateNotificationRuleRequest } from '../types';

export default function SettingsPage() {
  const { data: notifications, isLoading } = useNotifications();
  const createMutation = useCreateNotification();
  const updateMutation = useUpdateNotification();
  const deleteMutation = useDeleteNotification();

  const [showForm, setShowForm] = React.useState(false);
  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [formData, setFormData] = React.useState<Partial<CreateNotificationRuleRequest>>({
    channel: 'email',
    frequency: 'immediate',
    conditions: [],
  });

  const handleCreate = () => {
    createMutation.mutate(formData as CreateNotificationRuleRequest);
    setShowForm(false);
  };

  const handleUpdate = () => {
    if (editingId) {
      updateMutation.mutate({ id: editingId, data: formData });
      setEditingId(null);
    }
    setShowForm(false);
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Settings</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Notification rules, API keys, and platform configuration
          </p>
        </div>
        <button onClick={() => { setEditingId(null); setShowForm(true); }} className="btn-primary">
          <Plus size={16} /> Add Rule
        </button>
      </div>

      {/* Notification Rules */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-center gap-2 border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <Bell size={18} className="text-gray-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Notification Rules</h2>
        </div>

        {showForm && (
          <div className="border-b border-gray-200 p-6 dark:border-gray-700">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Name</label>
                <input
                  type="text"
                  className="mt-1 input"
                  value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Rule name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Channel</label>
                <select
                  className="mt-1 select"
                  value={formData.channel || 'email'}
                  onChange={(e) => setFormData({ ...formData, channel: e.target.value as any })}
                >
                  {NOTIFICATION_CHANNELS.map((ch) => (
                    <option key={ch.value} value={ch.value}>{ch.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Endpoint</label>
                <input
                  type="text"
                  className="mt-1 input"
                  value={formData.endpoint || ''}
                  onChange={(e) => setFormData({ ...formData, endpoint: e.target.value })}
                  placeholder="email@example.com or webhook URL"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Frequency</label>
                <select
                  className="mt-1 select"
                  value={formData.frequency || 'immediate'}
                  onChange={(e) => setFormData({ ...formData, frequency: e.target.value as any })}
                >
                  {NOTIFICATION_FREQUENCIES.map((f) => (
                    <option key={f.value} value={f.value}>{f.label}</option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end gap-3">
                <button onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
                <button onClick={editingId ? handleUpdate : handleCreate} className="btn-primary">
                  {editingId ? 'Update' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={24} className="animate-spin text-gray-400" />
          </div>
        ) : notifications?.length === 0 ? (
          <div className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">
            No notification rules configured
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {notifications?.map((rule) => (
              <div key={rule.id} className="flex items-center justify-between px-6 py-4">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{rule.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {rule.channel} • {rule.frequency}
                    {rule.endpoint && ` • ${rule.endpoint}`}
                  </p>
                  <p className="text-xs text-gray-400">
                    Last triggered: {rule.lastTriggeredAt ? formatDate(rule.lastTriggeredAt) : 'Never'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                    rule.enabled
                      ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                      : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
                  }`}>
                    {rule.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                  <button
                    onClick={() => { setEditingId(rule.id); setShowForm(true); }}
                    className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700"
                  >
                    <Edit size={14} />
                  </button>
                  <button
                    onClick={() => handleDelete(rule.id)}
                    className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
