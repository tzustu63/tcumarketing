import api from './api';

export const statsService = {
  // Get system statistics
  getStats: async () => {
    const response = await api.get('/api/stats');
    return response.data;
  },
};
