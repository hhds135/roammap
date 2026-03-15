import apiClient from './client';

export const postsApi = {
  create(data) {
    return apiClient.post('/posts', data);
  },

  get(postId) {
    return apiClient.get(`/posts/${postId}`);
  },

  update(postId, data) {
    return apiClient.put(`/posts/${postId}`, data);
  },

  delete(postId) {
    return apiClient.delete(`/posts/${postId}`);
  },

  list(params) {
    return apiClient.get('/posts', { params });
  },

  // Alias for list - get all posts with optional filters
  getAll(params) {
    return apiClient.get('/posts', { params });
  }
};