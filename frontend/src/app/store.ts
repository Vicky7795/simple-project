import { configureStore } from '@reduxjs/toolkit';
import interactionsReducer from '../features/interactions/interactionsSlice';
import hcpsReducer from '../features/hcps/hcpsSlice';
import chatReducer from '../features/chat/chatSlice';

export const store = configureStore({
  reducer: {
    interactions: interactionsReducer,
    hcps: hcpsReducer,
    chat: chatReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
