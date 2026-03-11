import apiClient from './client';
import { storage } from '../utils/storage';

export const authApi = {
  register(username, password) {
    return apiClient.post('/auth/register', {
      username,
      password,
    });
  },

  login(username, password) {
    return apiClient.post('/auth/login', {
      username,
      password,
    });
  },

  logout() {
    storage.clearAuth();
  }
};