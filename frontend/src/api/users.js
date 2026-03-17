import apiClient from './client';

export const usersApi = {
  getInterests(userId) {
    return apiClient.get(`/users/${userId}/interests`);
  },

  updateInterests(userId, tags) {
    return apiClient.put(`/users/${userId}/interests`, {
      interest_tags: tags
    });
  },

  updateProfile(userId, profile) {
    return apiClient.put(`/users/${userId}/profile`, profile);
  },

  search(query, params) {
    return apiClient.get('/users/search', {
      params: {
        q: query,
        ...params
      }
    });
  }
};