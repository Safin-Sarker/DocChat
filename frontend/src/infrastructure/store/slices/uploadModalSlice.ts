import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

interface UploadModalState {
  isOpen: boolean;
  isUploading: boolean;
}

const initialState: UploadModalState = {
  isOpen: false,
  isUploading: false,
};

const uploadModalSlice = createSlice({
  name: 'uploadModal',
  initialState,
  reducers: {
    openUploadModal(state) {
      state.isOpen = true;
    },
    closeUploadModal(state) {
      state.isOpen = false;
    },
    toggleUploadModal(state) {
      state.isOpen = !state.isOpen;
    },
    setUploading(state, action: PayloadAction<boolean>) {
      state.isUploading = action.payload;
    },
  },
});

export const { openUploadModal, closeUploadModal, toggleUploadModal, setUploading } =
  uploadModalSlice.actions;

export default uploadModalSlice.reducer;
