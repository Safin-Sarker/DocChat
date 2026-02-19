import { create } from 'zustand';

interface UploadModalStore {
  isOpen: boolean;
  isUploading: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
  setUploading: (uploading: boolean) => void;
}

export const useUploadModal = create<UploadModalStore>((set) => ({
  isOpen: false,
  isUploading: false,
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),
  toggle: () => set((state) => ({ isOpen: !state.isOpen })),
  setUploading: (uploading) => set({ isUploading: uploading }),
}));
