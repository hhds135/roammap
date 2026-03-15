import apiClient from './client';

export const favoritesApi = {
  // Favorite/unfavorite post
  toggle: (postId) => {
    return apiClient.post(`/posts/${postId}/favorite`);
  },

  // Get post favorites list
  getPostFavorites: (postId, params) => {
    return apiClient.get(`/posts/${postId}/favorites`, { params });
  },

  // Get user favorites list
  getUserFavorites: (userId, params) => {
    return apiClient.get(`/users/${userId}/favorites`, { params });
  }
};