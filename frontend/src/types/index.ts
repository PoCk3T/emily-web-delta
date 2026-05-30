export type Status = 'ACTIVE' | 'ERRORING' | 'DOWN' | 'DELETED' | 'UNREACHABLE';

export type Backend = 'firecrawl' | 'selfhosted';

export type DiffView = 'unified' | 'side-by-side' | 'json' | 'ai-summary';

export type CheckStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export type NotificationChannel = 'email' | 'webhook' | 'slack' | 'browser';

export type UserRole = 'user' | 'admin';

export type NotificationFrequency = 'immediate' | 'hourly' | 'daily' | 'weekly';

export interface Url {
  id: string;
  url: string;
  name: string;
  description: string;
  status: Status;
  backend: Backend;
  enabled: boolean;
  checkInterval: number;
  lastCheckedAt: string | null;
  lastStatus: Status;
  createdAt: string;
  updatedAt: string;
  tags: string[];
}

export interface CreateUrlRequest {
  url: string;
  name: string;
  description?: string;
  backend: Backend;
  checkInterval: number;
  tags?: string[];
}

export interface UpdateUrlRequest {
  url?: string;
  name?: string;
  description?: string;
  backend?: Backend;
  enabled?: boolean;
  checkInterval?: number;
  status?: Status;
  tags?: string[];
}

export interface CheckResult {
  id: string;
  urlId: string;
  status: CheckStatus;
  statusCode: number | null;
  contentLength: number | null;
  checksum: string | null;
  pageTitle: string | null;
  loadTime: number | null;
  error: string | null;
  startedAt: string;
  completedAt: string | null;
  createdAt: string;
}

export interface CreateCheckRequest {
  urlId: string;
}

export interface Diff {
  id: string;
  checkId: string;
  urlId: string;
  previousChecksum: string | null;
  currentChecksum: string | null;
  diffContent: string;
  diffType: 'html' | 'json' | 'text';
  summary: string | null;
  aiSummary: string | null;
  createdAt: string;
}

export interface CreateDiffRequest {
  checkId: string;
  urlId: string;
  diffContent: string;
  diffType: 'html' | 'json' | 'text';
}

export interface NotificationRule {
  id: string;
  name: string;
  urlId: string | null;
  channel: NotificationChannel;
  endpoint: string;
  frequency: NotificationFrequency;
  enabled: boolean;
  conditions: NotificationCondition[];
  lastTriggeredAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface NotificationCondition {
  type: 'status_change' | 'content_change' | 'down_alert' | 'frequency_anomaly';
  threshold?: number;
}

export interface CreateNotificationRuleRequest {
  name: string;
  urlId?: string;
  channel: NotificationChannel;
  endpoint: string;
  frequency: NotificationFrequency;
  conditions: NotificationCondition[];
}

export interface UpdateNotificationRuleRequest {
  name?: string;
  endpoint?: string;
  frequency?: NotificationFrequency;
  enabled?: boolean;
  conditions?: NotificationCondition[];
}

export interface AnalyticsData {
  urlId: string;
  changeFrequency: ChangeFrequencyData[];
  trend: TrendData;
  anomalies: AnomalyData[];
  totalChecks: number;
  totalDiffs: number;
  averageLoadTime: number;
  uptimePercentage: number;
}

export interface ChangeFrequencyData {
  date: string;
  changes: number;
}

export interface TrendData {
  direction: 'increasing' | 'decreasing' | 'stable';
  rate: number;
  confidence: number;
}

export interface AnomalyData {
  date: string;
  type: 'sudden_spike' | 'sudden_drop' | 'pattern_break';
  severity: 'low' | 'medium' | 'high';
  description: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  avatarUrl: string | null;
  createdAt: string;
  lastLoginAt: string | null;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

export interface PlatformStats {
  totalUrls: number;
  activeUrls: number;
  totalChecks: number;
  totalDiffs: number;
  totalUsers: number;
  activeUsers: number;
  checksToday: number;
  diffsToday: number;
  systemUptime: number;
  avgResponseTime: number;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  message: string;
  statusCode: number;
  details?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface PaginationParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  filter?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface ThemeState {
  dark: boolean;
  toggle: () => void;
}

export interface SidebarState {
  collapsed: boolean;
  toggle: () => void;
}

export interface ModalState {
  isOpen: boolean;
  title: string;
  body: React.ReactNode;
  onConfirm?: () => void;
  confirmLabel?: string;
  confirmVariant?: 'primary' | 'danger';
}
