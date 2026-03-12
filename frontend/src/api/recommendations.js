import apiClient from './client';

export const recommendationsApi = {
  // Get recommendation feed
  getFeed: (params) => {
    return apiClient.get('/feed', {
      params: { type: 'recommendation', ...params }
    });
  },

  // Get comprehensive feed
  getComprehensive: (params) => {
    return apiClient.get('/feed', {
      params: { type: 'all', ...params }
    });
  },

  // Get following feed
  getFollowing: (params) => {
    return apiClient.get('/feed', {
      params: { type: 'following', ...params }
    });
  },

  // Get recommendation config
  getConfig: () => {
    return apiClient.get('/feed/config');
  }
};