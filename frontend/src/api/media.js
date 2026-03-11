import apiClient from './client';

export const mediaApi = {
  upload(file, mediaType) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('media_type', mediaType);

    return apiClient.post('/media/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  getUrl(fileId) {
    return `http://localhost:5200/api/media/${fileId}`;
  },

  delete(fileId) {
    return apiClient.delete(`/media/${fileId}`);
  }
};