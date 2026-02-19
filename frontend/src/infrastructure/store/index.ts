import { combineReducers, configureStore } from '@reduxjs/toolkit';
import {
  persistStore,
  persistReducer,
  FLUSH,
  REHYDRATE,
  PAUSE,
  PERSIST,
  PURGE,
  REGISTER,
} from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import { createTransform } from 'redux-persist';
import authReducer from './slices/authSlice';
import chatReducer from './slices/chatSlice';
import uploadModalReducer from './slices/uploadModalSlice';
import themeReducer from './slices/themeSlice';
import { apiSlice } from './api/apiSlice';
import { setStoreRef } from './storeRef';

// Transform to exclude transient chat fields from persistence
const chatTransform = createTransform(
  // inbound: before saving
  (inboundState: Record<string, unknown>) => {
    const state = { ...inboundState };
    delete state.isLoading;
    delete state.streamingStage;
    return state;
  },
  // outbound: when rehydrating
  (outboundState: Record<string, unknown>) => ({
    ...outboundState,
    isLoading: false,
    streamingStage: null,
  }),
  { whitelist: ['chat'] }
);

const authPersistConfig = {
  key: 'auth-storage',
  storage,
};

const chatPersistConfig = {
  key: 'docchat-storage',
  storage,
  transforms: [chatTransform],
};

const themePersistConfig = {
  key: 'theme-storage',
  storage,
};

const rootReducer = combineReducers({
  auth: persistReducer(authPersistConfig, authReducer),
  chat: persistReducer(chatPersistConfig, chatReducer),
  uploadModal: uploadModalReducer,
  theme: persistReducer(themePersistConfig, themeReducer),
  [apiSlice.reducerPath]: apiSlice.reducer,
});

export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
      },
    }).concat(apiSlice.middleware),
});

export const persistor = persistStore(store);

// Set the mutable store ref so non-React code can access it
setStoreRef(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export type AppStore = typeof store;
