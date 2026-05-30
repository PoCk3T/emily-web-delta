import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar />
      <div className="flex flex-col min-h-screen transition-all duration-200">
        <Header />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
