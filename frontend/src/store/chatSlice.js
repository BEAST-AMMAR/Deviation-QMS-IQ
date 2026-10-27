import { createSlice } from '@reduxjs/toolkit';

/*
 * Chat Slice — message list + loading/in-flight state
 * Per TDD §6.
 */

const initialState = {
  messages: [
    {
      role: 'assistant',
      content: 'Welcome to DeviationIQ.\n\nI can extract structured deviation data from your incident reports automatically. Upload a document or paste report text to get started.',
      timestamp: new Date().toISOString(),
    },
  ],
  isProcessing: false,
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addMessage(state, action) {
      state.messages.push({
        ...action.payload,
        timestamp: action.payload.timestamp || new Date().toISOString(),
      });
    },

    setProcessing(state, action) {
      state.isProcessing = action.payload;
    },

    clearMessages(state) {
      state.messages = [initialState.messages[0]];
    },
  },
});

export const { addMessage, setProcessing, clearMessages } = chatSlice.actions;
export default chatSlice.reducer;
