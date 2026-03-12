import apiClient from './client';

export const cornersApi = {
  // Get nearby corners
  getNearby: (params) => {
    return apiClient.get('/corners/nearby', { params });
  },

  // Get corner details
  get: (cornerId) => {
    return apiClient.get(`/corners/${cornerId}`);
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

  // Get aggregated info for multiple corners
  aggregate: (cornerIds) => {
    return apiClient.get('/corners/aggregate', {
      params: { corner_ids: cornerIds.join(',') }
    });
  }
};