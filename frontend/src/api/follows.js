import apiClient from './client';

export const followsApi = {
  follow(userId) {
    return apiClient.post(`/follows/${userId}`);
  },

  unfollow(userId) {
    return apiClient.delete(`/follows/${userId}`);
  },

  getFollowing(userId, params) {
    return apiClient.get(`/users/${userId}/following`, { params });
  },

  getFollowers(userId, params) {
    return apiClient.get(`/users/${userId}/followers`, { params });
  },

  getStatus(userId) {
    return apiClient.get(`/follows/${userId}/status`);
  }
};