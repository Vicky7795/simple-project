import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export interface HCP {
  id: number;
  name: string;
  specialty?: string;
  hospital_affiliation?: string;
  email?: string;
  phone?: string;
  preferred_channel?: string;
  notes?: string;
  created_at: string;
}

interface HcpsState {
  list: HCP[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: HcpsState = {
  list: [],
  status: 'idle',
  error: null,
};

export const fetchHcps = createAsyncThunk(
  'hcps/fetchHcps',
  async (search?: string) => {
    const url = search ? `${API_BASE}/hcps?search=${encodeURIComponent(search)}` : `${API_BASE}/hcps`;
    const response = await axios.get(url);
    return response.data as HCP[];
  }
);

export const createHcp = createAsyncThunk(
  'hcps/createHcp',
  async (hcpData: Omit<HCP, 'id' | 'created_at'>) => {
    const response = await axios.post(`${API_BASE}/hcps`, hcpData);
    return response.data as HCP;
  }
);

const hcpsSlice = createSlice({
  name: 'hcps',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchHcps.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchHcps.fulfilled, (state, action: PayloadAction<HCP[]>) => {
        state.status = 'succeeded';
        state.list = action.payload;
      })
      .addCase(fetchHcps.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Failed to fetch HCPs';
      })
      .addCase(createHcp.fulfilled, (state, action: PayloadAction<HCP>) => {
        state.list.push(action.payload);
      });
  },
});

export default hcpsSlice.reducer;
