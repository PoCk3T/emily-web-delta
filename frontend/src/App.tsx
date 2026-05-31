import React, { Suspense, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { useUiStore } from './store/uiStore';
import { ROUTES } from './lib/constants';
import { Layout } from './components/layout/Layout';
import DashboardPage from './pages/dashboard';
import UrlListPage from './pages/url-list';
import UrlDetailPage from './pages/url-detail';
import ChecksPage from './pages/checks';
import DiffsPage from './pages/diffs';
import AnalyticsPage from './pages/analytics';
import SettingsPage from './pages/settings';
import AdminPage from './pages/admin';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, initialize } = useAuthStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function LoginScreen() {
  const { isAuthenticated, initialize, login, isLoading } = useAuthStore();
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [error, setError] = React.useState<string | null>(null);

  useEffect(() => {
    initialize();
  }, [initialize]);

  if (isAuthenticated) {
    return <Navigate to={ROUTES.dashboard} replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Login failed');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-md rounded-xl border border-gray-200 bg-white p-8 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-brand-600">
            <span className="text-xl font-bold text-white">E</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Emily Web Delta</h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Web page change monitoring platform
          </p>
        </div>
        <form className="space-y-4" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/30 dark:text-red-400">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Email</label>
            <input
              type="email"
              className="mt-1 input"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Password</label>
            <input
              type="password"
              className="mt-1 input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn-primary w-full" disabled={isLoading}>
            {isLoading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
          Don't have an account?{' '}
          <a href="/register" className="font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400">
            Sign up
          </a>
        </p>
      </div>
    </div>
  );
}

function App() {
  const { theme } = useUiStore();

  React.useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  return (
    <Routes>
      <Route path="/login" element={<LoginScreen />} />
      <Route
        path="/*"
        element={
          <RequireAuth>
            <Layout>
              <Suspense fallback={<div className="p-6 text-center text-gray-500">Loading...</div>}>
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path={ROUTES.urls} element={<UrlListPage />} />
                  <Route path={ROUTES.urlDetail} element={<UrlDetailPage />} />
                  <Route path={ROUTES.checks} element={<ChecksPage />} />
                  <Route path={ROUTES.diffs} element={<DiffsPage />} />
                  <Route path={ROUTES.analytics} element={<AnalyticsPage />} />
                  <Route path={ROUTES.settings} element={<SettingsPage />} />
                  <Route path={ROUTES.admin} element={<AdminPage />} />
                  <Route path="*" element={<Navigate to={ROUTES.dashboard} replace />} />
                </Routes>
              </Suspense>
            </Layout>
          </RequireAuth>
        }
      />
    </Routes>
  );
}

export default App;
