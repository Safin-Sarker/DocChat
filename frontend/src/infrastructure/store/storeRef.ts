import type { AppStore } from './index';

let store: AppStore | null = null;

export const getStore = (): AppStore => {
  if (!store) throw new Error('Store not initialized');
  return store;
};

export const setStoreRef = (s: AppStore) => {
  store = s;
};
