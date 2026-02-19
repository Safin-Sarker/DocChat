import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

type Theme = 'light' | 'dark' | 'system';

interface ThemeState {
  theme: Theme;
}

const initialState: ThemeState = {
  theme: 'system',
};

const themeSlice = createSlice({
  name: 'theme',
  initialState,
  reducers: {
    setTheme(state, action: PayloadAction<Theme>) {
      state.theme = action.payload;
    },
    toggleTheme(state) {
      const isDark =
        state.theme === 'dark' ||
        (state.theme === 'system' &&
          window.matchMedia('(prefers-color-scheme: dark)').matches);
      state.theme = isDark ? 'light' : 'dark';
    },
  },
});

export const { setTheme, toggleTheme } = themeSlice.actions;
export default themeSlice.reducer;
