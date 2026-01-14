// src/api/market.js
import apiClient from './client';

export const marketAPI = {
  getPrice: async (symbol, assetType) => {
    const response = await apiClient.get(`/market/price/${symbol}`, {
      params: { asset_type: assetType },
    });
    return response.data;
  },

  getMultiplePrices: async (symbols, assetType) => {
    const response = await apiClient.post('/market/prices', {
      symbols,
      asset_type: assetType,
    });
    return response.data;
  },

  validateSymbol: async (symbol, assetType) => {
    const response = await apiClient.get(`/market/validate/${symbol}`, {
      params: { asset_type: assetType },
    });
    return response.data;
  },
};