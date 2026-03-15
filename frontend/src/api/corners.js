import apiClient from './client';

export const cornersApi = {
  // Create corner
  create: (data) => {
    return apiClient.post('/corners', data);
  },

  // Get all corners
  getAll: (params) => {
    return apiClient.get('/corners', { params });
  },

  // Get nearby corners
  getNearby: (params) => {
    return apiClient.get('/corners/nearby', { params });
  },

  // Get corner details
  get: (cornerId) => {
    return apiClient.get(`/corners/${cornerId}`);
  },

  // Update corner
  update: (cornerId, data) => {
    return apiClient.put(`/corners/${cornerId}`, data);
  },

  // Get posts associated with corner
  getPosts: (cornerId, params) => {
    return apiClient.get(`/corners/${cornerId}/posts`, { params });
  },

  // Search corners
  search: (query, params) => {
    return apiClient.get('/corners/search', {
      params: { q: query, ...params }
    });
  },

  // Get aggregate information for multiple corners
  aggregate: (cornerIds) => {
    return apiClient.get('/corners/aggregate', {
      params: { corner_ids: cornerIds.join(',') }
    });
  }
};