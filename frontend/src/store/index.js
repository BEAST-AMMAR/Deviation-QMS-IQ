import { configureStore } from '@reduxjs/toolkit';
import { apiSlice } from './apiSlice';
import draftReducer from './draftSlice';
import chatReducer from './chatSlice';

export const store = configureStore({
  reducer: {
    draft: draftReducer,
    chat: chatReducer,
    [apiSlice.reducerPath]: apiSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(apiSlice.middleware),
});
