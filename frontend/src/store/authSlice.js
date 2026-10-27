import { createSlice } from '@reduxjs/toolkit';

const rawToken = localStorage.getItem('deviationiq_token');
let validToken = null;
if (
  rawToken &&
  rawToken !== 'null' &&
  rawToken !== 'undefined' &&
  typeof rawToken === 'string' &&
  rawToken.split('.').length === 3
) {
  validToken = rawToken;
} else if (rawToken) {
  localStorage.removeItem('deviationiq_token');
}

let initialUser = null;
try {
  const storedUser = localStorage.getItem('deviationiq_user');
  if (storedUser && storedUser !== 'null' && storedUser !== 'undefined') {
    const parsed = JSON.parse(storedUser);
    if (parsed && typeof parsed === 'object') {
      initialUser = parsed;
    }
  }
} catch {
  initialUser = null;
  localStorage.removeItem('deviationiq_user');
}

// User is strictly considered authenticated only if both a valid JWT token and user profile exist
const isAuthenticated = Boolean(validToken && initialUser);

const initialState = {
  token: isAuthenticated ? validToken : null,
  user: isAuthenticated ? initialUser : null,
  isAuthenticated,
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

