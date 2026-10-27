import { configureStore } from '@reduxjs/toolkit';
import { apiSlice } from './apiSlice';
import draftReducer from './draftSlice';
import chatReducer from './chatSlice';
import authReducer from './authSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    draft: draftReducer,
    chat: chatReducer,
    [apiSlice.reducerPath]: apiSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(apiSlice.middleware),
});
