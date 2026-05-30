import { create } from 'zustand';

interface UiState {
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleTheme: () => void;
}

const getStoredTheme = (): 'light' | 'dark' => {
  try {
    const stored = localStorage.getItem('emily-theme');
    if (stored === 'dark' || stored === 'light') return stored;
  } catch {
    // Storage unavailable
  }
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
};

const applyTheme = (theme: 'light' | 'dark'): void => {
  if (typeof document !== 'undefined') {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }
};

export const useUiStore = create<UiState>((set) => ({
  sidebarCollapsed: false,
  theme: getStoredTheme(),

  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  setTheme: (theme) => {
    applyTheme(theme);
    try {
      localStorage.setItem('emily-theme', theme);
    } catch {
      // Storage unavailable
    }
    set({ theme });
  },

  toggleTheme: () => set((state) => {
    const newTheme = state.theme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
    try {
      localStorage.setItem('emily-theme', newTheme);
    } catch {
      // Storage unavailable
    }
    return { theme: newTheme };
  }),
}));
