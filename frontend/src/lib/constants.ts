export const APP_NAME = 'Emily Web Delta';
export const APP_VERSION = '1.0.0';
export const API_VERSION = 'v1';

export const CHECK_INTERVALS = [
  { value: 5, label: 'Every 5 minutes' },
  { value: 15, label: 'Every 15 minutes' },
  { value: 30, label: 'Every 30 minutes' },
  { value: 60, label: 'Every hour' },
  { value: 120, label: 'Every 2 hours' },
  { value: 360, label: 'Every 6 hours' },
  { value: 720, label: 'Every 12 hours' },
  { value: 1440, label: 'Every day' },
];

export const NOTIFICATION_CHANNELS = [
  { value: 'email', label: 'Email' },
  { value: 'webhook', label: 'Webhook' },
  { value: 'slack', label: 'Slack' },
  { value: 'browser', label: 'Browser Notification' },
] as const;

export const NOTIFICATION_FREQUENCIES = [
  { value: 'immediate', label: 'Immediate' },
  { value: 'hourly', label: 'Hourly Digest' },
  { value: 'daily', label: 'Daily Digest' },
  { value: 'weekly', label: 'Weekly Digest' },
] as const;

export const NOTIFICATION_CONDITIONS = [
  { value: 'status_change', label: 'Status Change' },
  { value: 'content_change', label: 'Content Change' },
  { value: 'down_alert', label: 'Down Alert' },
  { value: 'frequency_anomaly', label: 'Frequency Anomaly' },
] as const;

export const ROUTES = {
  dashboard: '/',
  urls: '/urls',
  urlDetail: '/urls/:id',
  checks: '/checks',
  diffs: '/diffs',
  analytics: '/analytics',
  settings: '/settings',
  admin: '/admin',
} as const;

export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
} as const;

export const STORAGE_KEYS = {
  THEME: 'emily-theme',
  SIDEBAR_COLLAPSED: 'emily-sidebar-collapsed',
  AUTH_TOKEN: 'emily-auth-token',
} as const;
