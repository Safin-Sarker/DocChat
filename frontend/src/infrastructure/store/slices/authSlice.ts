import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { UserInfo } from '@/domain/auth/types';

interface AuthState {
  user: UserInfo | null;
  token: string | null;
  isAuthenticated: boolean;
}

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setAuth(state, action: PayloadAction<{ token: string; user: UserInfo }>) {
      state.token = action.payload.token;
      state.user = action.payload.user;
      state.isAuthenticated = true;
    },
    logout() {
      return initialState;
    },
  },
});

export const { setAuth, logout } = authSlice.actions;
export default authSlice.reducer;
