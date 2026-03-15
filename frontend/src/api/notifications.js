import apiClient from './client';

export const notificationsApi = {
  // Get notifications list
  getAll: (params) => {
    return apiClient.get('/notifications', { params });
  },

  // Get unread notifications count
  getUnreadCount: () => {
    return apiClient.get('/notifications/unread-count');
  },

  // Mark notification as read
  markAsRead: (notificationId) => {
    return apiClient.put(`/notifications/${notificationId}/read`);
  },

  // Mark all notifications as read
  markAllAsRead: () => {
    return apiClient.put('/notifications/read-all');
  },

  // Delete notification
  delete: (notificationId) => {
    return apiClient.delete(`/notifications/${notificationId}`);
  }
};