import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Globe,
  Activity,
  GitCompare,
  BarChart3,
  Bell,
  Settings,
  Shield,
  Moon,
  Sun,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useUiStore } from '../../store/uiStore';
import { ROUTES } from '../../lib/constants';

interface NavItem {
  name: string;
  href: string;
  icon: React.FC<{ className?: string; size?: number | string }>;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', href: ROUTES.dashboard, icon: LayoutDashboard },
  { name: 'URLs', href: ROUTES.urls, icon: Globe },
  { name: 'Checks', href: ROUTES.checks, icon: Activity },
  { name: 'Diffs', href: ROUTES.diffs, icon: GitCompare },
  { name: 'Analytics', href: ROUTES.analytics, icon: BarChart3 },
  { name: 'Notifications', href: ROUTES.settings, icon: Bell },
  { name: 'Settings', href: ROUTES.settings, icon: Settings },
  { name: 'Admin', href: ROUTES.admin, icon: Shield, adminOnly: true },
];

export function Sidebar() {
  const location = useLocation();
  const { sidebarCollapsed, toggleSidebar } = useUiStore();

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex flex-col bg-white border-r border-gray-200 transition-all duration-200 dark:bg-gray-800 dark:border-gray-700 ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-gray-200 dark:border-gray-700">
        {!sidebarCollapsed && (
          <Link to={ROUTES.dashboard} className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
              <span className="text-sm font-bold text-white">E</span>
            </div>
            <span className="text-lg font-semibold text-gray-900 dark:text-white">Emily Delta</span>
          </Link>
        )}
        <button
          onClick={toggleSidebar}
          className="rounded-md p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = location.pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              to={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-700/50 dark:hover:text-gray-200'
              }`}
              title={sidebarCollapsed ? item.name : undefined}
            >
              <Icon size={20} />
              {!sidebarCollapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Theme toggle */}
      <div className="border-t border-gray-200 p-3 dark:border-gray-700">
        <ThemeToggle collapsed={sidebarCollapsed} />
      </div>
    </aside>
  );
}

function ThemeToggle({ collapsed }: { collapsed: boolean }) {
  const { theme, toggleTheme } = useUiStore();
  const isDark = theme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-700/50 dark:hover:text-gray-200"
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? <Sun size={20} /> : <Moon size={20} />}
      {!collapsed && <span>{isDark ? 'Light Mode' : 'Dark Mode'}</span>}
    </button>
  );
}
