import apiClient from './client';

export const feedApi = {
  getFollowing(params) {
    return apiClient.get('/feed/following', { params });
  },

  getStatus() {
    return apiClient.get('/feed/status');
  }
};