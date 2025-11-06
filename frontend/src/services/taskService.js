import api from './api';

export const taskService = {
  // Create new task
  createTask: async (taskData) => {
    const response = await api.post('/api/tasks', taskData);
    return response.data;
  },

  // Get all tasks
  getTasks: async (params = {}) => {
    const response = await api.get('/api/tasks', { params });
    return response.data;
  },

  // Get task by ID
  getTask: async (taskId) => {
    const response = await api.get(`/api/tasks/${taskId}`);
    return response.data;
  },

  // Start task
  startTask: async (taskId) => {
    const response = await api.post(`/api/tasks/${taskId}/start`);
    return response.data;
  },

  // Delete task
  deleteTask: async (taskId) => {
    const response = await api.delete(`/api/tasks/${taskId}`);
    return response.data;
  },
};
