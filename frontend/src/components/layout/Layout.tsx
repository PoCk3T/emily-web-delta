import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useUiStore } from '../../store/uiStore';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { sidebarCollapsed } = useUiStore();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar />
      <div 
        className="flex flex-col min-h-screen transition-all duration-200"
        style={{ paddingLeft: sidebarCollapsed ? '4rem' : '16rem' }}
      >
        <Header />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
