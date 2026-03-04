import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { UserInfo } from '@/domain/auth/types';

interface AuthState {
  user: UserInfo | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}

const initialState: AuthState = {
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setAuth(state, action: PayloadAction<{ token: string; refreshToken: string; user: UserInfo }>) {
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken;
      state.user = action.payload.user;
      state.isAuthenticated = true;
    },
    setTokens(state, action: PayloadAction<{ token: string; refreshToken: string }>) {
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken;
    },
    logout() {
      return initialState;
    },
  },
});

export const { setAuth, setTokens, logout } = authSlice.actions;
export default authSlice.reducer;
