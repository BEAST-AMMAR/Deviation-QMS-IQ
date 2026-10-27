import { createSlice } from '@reduxjs/toolkit';

const initialToken = localStorage.getItem('deviationiq_token');
let initialUser = null;
try {
  const storedUser = localStorage.getItem('deviationiq_user');
  if (storedUser) {
    initialUser = JSON.parse(storedUser);
  }
} catch {
  initialUser = null;
}

const initialState = {
  token: initialToken || null,
  user: initialUser,
  isAuthenticated: Boolean(initialToken),
};

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (state, action) => {
      const { access_token, user } = action.payload;
      state.token = access_token;
      state.user = user;
      state.isAuthenticated = true;
      localStorage.setItem('deviationiq_token', access_token);
      localStorage.setItem('deviationiq_user', JSON.stringify(user));
    },
    logout: (state) => {
      state.token = null;
      state.user = null;
      state.isAuthenticated = false;
      localStorage.removeItem('deviationiq_token');
      localStorage.removeItem('deviationiq_user');
    },
  },
});

export const { setCredentials, logout } = authSlice.actions;
export default authSlice.reducer;

