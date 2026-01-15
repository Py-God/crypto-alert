// src/api/alerts.js
import apiClient from './client';

export const alertsAPI = {
  // Get all alerts with pagination and filters
  getAlerts: async (page = 1, pageSize = 100, status = null, assetType = null) => {
    const params = { page, page_size: pageSize };
    if (status) params.status = status;
    if (assetType) params.asset_type = assetType;
    
    const response = await apiClient.get('/alerts', { params });
    return response.data;
  },

  // Get alert statistics
  getAlertStats: async () => {
    const response = await apiClient.get('/alerts/stats');
    return response.data;
  },

  // Create new alert
  createAlert: async (data) => {
    const response = await apiClient.post('/alerts', data);
    return response.data;
  },

  // Update existing alert
  updateAlert: async (id, data) => {
    const response = await apiClient.put(`/alerts/${id}`, data);
    return response.data;
  },

  // Delete alert
  deleteAlert: async (id) => {
    const response = await apiClient.delete(`/alerts/${id}`);
    return response.data;
  },

  // Get single alert by ID
  getAlert: async (id) => {
    const response = await apiClient.get(`/alerts/${id}`);
    return response.data;
  }
};