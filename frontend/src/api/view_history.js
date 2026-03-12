import apiClient from './client';

export const viewHistoryApi = {
  // Record post view
  recordView: (postId, viewDuration) => {
    return apiClient.post(`/posts/${postId}/view`, {
      view_duration: viewDuration
    });
  },

  // Get user view history
  getUserHistory: (userId, params) => {
    return apiClient.get(`/users/${userId}/view-history`, { params });
  },

  // Get post view statistics
  getPostStats: (postId) => {
    return apiClient.get(`/posts/${postId}/view-stats`);
  }
};