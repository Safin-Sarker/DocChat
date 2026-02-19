import { useEffect, useCallback } from 'react';
import { useAppSelector, useAppDispatch } from '@/infrastructure/store/hooks';
import { setTheme as setThemeAction, toggleTheme as toggleThemeAction } from '@/infrastructure/store/slices/themeSlice';

type Theme = 'light' | 'dark' | 'system';

export function useTheme() {
  const theme = useAppSelector((s) => s.theme.theme);
  const dispatch = useAppDispatch();

  const setTheme = useCallback(
    (t: Theme) => dispatch(setThemeAction(t)),
    [dispatch]
  );

  const toggleTheme = useCallback(
    () => dispatch(toggleThemeAction()),
    [dispatch]
  );

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
