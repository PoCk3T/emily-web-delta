import React from 'react';
import { Shield, Users, Database, Server, Settings, Key, AlertCircle } from 'lucide-react';

export default function AdminPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">Admin Panel</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          System configuration, user management, and infrastructure monitoring
        </p>
      </div>

      {/* System Status */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-50 dark:bg-emerald-900/20">
              <Server size={20} className="text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">API Server</p>
              <p className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">Online</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 dark:bg-blue-900/20">
              <Database size={20} className="text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Database</p>
              <p className="text-sm font-semibold text-blue-600 dark:text-blue-400">Connected</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-50 dark:bg-purple-900/20">
              <Key size={20} className="text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">API Keys</p>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">Manage</p>
            </div>
          </div>
        </div>
      </div>

      {/* Admin Actions */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
          <Settings size={20} /> Admin Actions
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <button className="flex items-center gap-3 rounded-lg border border-gray-200 p-4 text-left transition-colors hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700">
            <Users size={20} className="text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">User Management</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Manage users and roles</p>
            </div>
          </button>
          <button className="flex items-center gap-3 rounded-lg border border-gray-200 p-4 text-left transition-colors hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700">
            <Shield size={20} className="text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">Security Settings</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Auth, CORS, rate limits</p>
            </div>
          </button>
          <button className="flex items-center gap-3 rounded-lg border border-gray-200 p-4 text-left transition-colors hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700">
            <AlertCircle size={20} className="text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">System Health</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Monitor services</p>
            </div>
          </button>
        </div>
      </div>

      {/* Configuration */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">System Configuration</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2 dark:bg-gray-700">
            <span className="text-sm text-gray-600 dark:text-gray-300">Firecrawl API</span>
            <span className="text-xs font-mono text-gray-400">••••••••</span>
          </div>
          <div className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2 dark:bg-gray-700">
            <span className="text-sm text-gray-600 dark:text-gray-300">SMTP Server</span>
            <span className="text-xs text-gray-400">Not configured</span>
          </div>
          <div className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2 dark:bg-gray-700">
            <span className="text-sm text-gray-600 dark:text-gray-300">Celery Workers</span>
            <span className="text-xs font-mono text-emerald-500">Running</span>
          </div>
        </div>
      </div>
    </div>
  );
}
