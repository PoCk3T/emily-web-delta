import { create } from 'zustand';
import type { Url } from '../types';

interface UrlState {
  urls: Url[];
  selectedUrlId: string | null;
  setUrls: (urls: Url[]) => void;
  setSelectedUrlId: (id: string | null) => void;
  addUrl: (url: Url) => void;
  updateUrl: (id: string, updates: Partial<Url>) => void;
  deleteUrl: (id: string) => void;
}

export const useUrlStore = create<UrlState>((set) => ({
  urls: [],
  selectedUrlId: null,
  setUrls: (urls) => set({ urls }),
  setSelectedUrlId: (id) => set({ selectedUrlId: id }),
  addUrl: (url) => set((state) => ({ urls: [...state.urls, url] })),
  updateUrl: (id, updates) =>
    set((state) => ({
      urls: state.urls.map((u) => (u.id === id ? { ...u, ...updates } : u)),
    })),
  deleteUrl: (id) =>
    set((state) => ({
      urls: state.urls.filter((u) => u.id !== id),
      selectedUrlId: state.selectedUrlId === id ? null : state.selectedUrlId,
    })),
}));
