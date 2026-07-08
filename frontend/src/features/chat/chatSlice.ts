import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponseData {
  reply: string;
  intent: string;
  tool_used?: string;
  tool_result?: any;
  interaction_id?: number;
}

interface ChatState {
  threadId: string;
  messages: ChatMessage[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
  lastAgentResponse: ChatResponseData | null;
}

// Helper to generate a random session thread ID
const generateThreadId = () => {
  return 'thread_' + Math.random().toString(36).substring(2, 11);
};

const initialState: ChatState = {
  threadId: generateThreadId(),
  messages: [],
  status: 'idle',
  error: null,
  lastAgentResponse: null,
};

export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async ({ thread_id, message }: { thread_id: string; message: string }) => {
    const response = await axios.post(`${API_BASE}/agent/chat`, {
      thread_id,
      user_id: 1,
      message,
    });
    return response.data as ChatResponseData;
  }
);

export const fetchChatHistory = createAsyncThunk(
  'chat/fetchChatHistory',
  async (thread_id: string) => {
    const response = await axios.get(`${API_BASE}/agent/sessions/${thread_id}/history`);
    return response.data.messages as ChatMessage[];
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    resetSession: (state) => {
      state.threadId = generateThreadId();
      state.messages = [];
      state.lastAgentResponse = null;
      state.status = 'idle';
    },
    addLocalUserMessage: (state, action: PayloadAction<string>) => {
      state.messages.push({ role: 'user', content: action.payload });
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(sendMessage.fulfilled, (state, action: PayloadAction<ChatResponseData>) => {
        state.status = 'succeeded';
        state.messages.push({ role: 'assistant', content: action.payload.reply });
        state.lastAgentResponse = action.payload;
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Failed to communicate with agent';
      })
      .addCase(fetchChatHistory.fulfilled, (state, action: PayloadAction<ChatMessage[]>) => {
        state.messages = action.payload;
      });
  },
});

export const { resetSession, addLocalUserMessage } = chatSlice.actions;
export default chatSlice.reducer;
