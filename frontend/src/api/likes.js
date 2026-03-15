import apiClient from './client';

export const likesApi = {
  // Like or unlike post
  toggle: (postId) => {
    return apiClient.post(`/posts/${postId}/like`);
  },

  // Get post likes list
  getPostLikes: (postId, params) => {
    return apiClient.get(`/posts/${postId}/likes`, { params });
  },

  // Get user liked posts
  getUserLikes: (userId, params) => {
    return apiClient.get(`/users/${userId}/likes`, { params });
  }
};