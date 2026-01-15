// src/api/market.js
import apiClient from './client';

export const marketAPI = {
  // Get single price
  getPrice: async (symbol, assetType) => {
    const response = await apiClient.get(`/market/price/${symbol}`, {
      params: { asset_type: assetType },
    });
    return response.data;
  },

  // Get multiple prices (batch)
  getMultiplePrices: async (symbols, assetType) => {
    const response = await apiClient.post('/market/prices', {
      symbols,
      asset_type: assetType,
    });
    return response.data;
  },

  // Validate symbol
  validateSymbol: async (symbol, assetType) => {
    const response = await apiClient.get(`/market/validate/${symbol}`, {
      params: { asset_type: assetType },
    });
    return response.data;
  },
};