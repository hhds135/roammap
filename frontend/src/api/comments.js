import apiClient from './client';

export const commentsApi = {
  // Add comment
  add: (postId, content) => {
    return apiClient.post(`/posts/${postId}/comments`, { content });
  },

  // Get post comments list
  getPostComments: (postId, params) => {
    return apiClient.get(`/posts/${postId}/comments`, { params });
  },

  // Delete comment
  delete: (commentId) => {
    return apiClient.delete(`/comments/${commentId}`);
  },

  // Get user comments
  getUserComments: (userId, params) => {
    return apiClient.get(`/users/${userId}/comments`, { params });
  }
};