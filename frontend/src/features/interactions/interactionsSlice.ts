import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';
import { HCP } from '../hcps/hcpsSlice';

let API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';
if (API_BASE && !API_BASE.endsWith('/api')) {
  API_BASE = `${API_BASE}/api`;
}

export interface Interaction {
  id: number;
  hcp_id: number;
  user_id: number;
  interaction_type: string;
  interaction_date?: string;
  channel?: string;
  topics_discussed: string[];
  products_discussed: string[];
  sentiment?: string;
  summary?: string;
  raw_input?: string;
  source: string;
  follow_up_required: boolean;
  follow_up_date?: string;
  samples_distributed?: Record<string, number>;
  created_at: string;
  updated_at: string;
  hcp?: HCP;
}

export interface FollowUp {
  id: number;
  hcp_name: string;
  specialty?: string;
  interaction_id: number;
  follow_up_date: string;
  topics: string[];
  products: string[];
}

interface InteractionsState {
  list: Interaction[];
  followUps: FollowUp[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  followUpsStatus: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: InteractionsState = {
  list: [],
  followUps: [],
  status: 'idle',
  followUpsStatus: 'idle',
  error: null,
};

export const fetchInteractions = createAsyncThunk(
  'interactions/fetchInteractions',
  async (filters?: { hcp_id?: number; user_id?: number }) => {
    let url = `${API_BASE}/interactions`;
    const params = new URLSearchParams();
    if (filters?.hcp_id) params.append('hcp_id', String(filters.hcp_id));
    if (filters?.user_id) params.append('user_id', String(filters.user_id));
    const qs = params.toString();
    if (qs) url += `?${qs}`;
    
    const response = await axios.get(url);
    return response.data as Interaction[];
  }
);

export const logInteraction = createAsyncThunk(
  'interactions/logInteraction',
  async (data: Omit<Interaction, 'id' | 'user_id' | 'created_at' | 'updated_at' | 'hcp'>) => {
    const response = await axios.post(`${API_BASE}/interactions`, data);
    return response.data as Interaction;
  }
);

export const editInteraction = createAsyncThunk(
  'interactions/editInteraction',
  async ({ id, data }: { id: number; data: Partial<Interaction> }) => {
    const response = await axios.put(`${API_BASE}/interactions/${id}`, data);
    return response.data as Interaction;
  }
);

export const fetchFollowUps = createAsyncThunk(
  'interactions/fetchFollowUps',
  async () => {
    const response = await axios.get(`${API_BASE}/followups`);
    return response.data as FollowUp[];
  }
);

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchInteractions.fulfilled, (state, action: PayloadAction<Interaction[]>) => {
        state.status = 'succeeded';
        state.list = action.payload;
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Failed to fetch interactions';
      })
      .addCase(logInteraction.fulfilled, (state, action: PayloadAction<Interaction>) => {
        state.list.unshift(action.payload); // Prepend new interaction
      })
      .addCase(editInteraction.fulfilled, (state, action: PayloadAction<Interaction>) => {
        const index = state.list.findIndex(item => item.id === action.payload.id);
        if (index !== -1) {
          state.list[index] = action.payload;
        }
      })
      .addCase(fetchFollowUps.pending, (state) => {
        state.followUpsStatus = 'loading';
      })
      .addCase(fetchFollowUps.fulfilled, (state, action: PayloadAction<FollowUp[]>) => {
        state.followUpsStatus = 'succeeded';
        state.followUps = action.payload;
      })
      .addCase(fetchFollowUps.rejected, (state) => {
        state.followUpsStatus = 'failed';
      });
  },
});

export default interactionsSlice.reducer;
