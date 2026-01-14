// src/api/alerts.js
import apiClient from './client';

export const alertsAPI = {
  getAlerts: async (page = 1, pageSize = 20, status = null) => {
    const params = { page, page_size: pageSize };
    if (status) params.status_filter = status;
    
    const response = await apiClient.get('/alerts', { params });
    return response.data;
  },

  getAlert: async (alertId) => {
    const response = await apiClient.get(`/alerts/${alertId}`);
    return response.data;
  },

  createAlert: async (alertData) => {
    const response = await apiClient.post('/alerts', alertData);
    return response.data;
  },

  updateAlert: async (alertId, alertData) => {
    const response = await apiClient.put(`/alerts/${alertId}`, alertData);
    return response.data;
  },

  deleteAlert: async (alertId) => {
    await apiClient.delete(`/alerts/${alertId}`);
  },

  getStats: async () => {
    const response = await apiClient.get('/alerts/stats');
    return response.data;
  },
};