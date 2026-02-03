import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { useEffect } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeStore {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      theme: 'system',

      setTheme: (theme) => set({ theme }),

      toggleTheme: () => {
        const current = get().theme;
        const isDark =
          current === 'dark' ||
          (current === 'system' &&
            window.matchMedia('(prefers-color-scheme: dark)').matches);
        set({ theme: isDark ? 'light' : 'dark' });
      },
    }),
    {
      name: 'theme-storage',
    }
  )
);

export function useTheme() {
  const { theme, setTheme, toggleTheme } = useThemeStore();

  useEffect(() => {
    const root = window.document.documentElement;

    const applyTheme = () => {
      root.classList.remove('light', 'dark');

      if (theme === 'system') {
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)')
          .matches
          ? 'dark'
          : 'light';
        root.classList.add(systemTheme);
      } else {
        root.classList.add(theme);
      }
    };

    applyTheme();

    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handler = () => applyTheme();
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    }
  }, [theme]);

  return { theme, setTheme, toggleTheme };
}
