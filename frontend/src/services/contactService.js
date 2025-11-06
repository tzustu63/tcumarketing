import api from './api';

export const contactService = {
  // Get all contacts with filters
  getContacts: async (params = {}) => {
    const response = await api.get('/api/contacts', { params });
    return response.data;
  },

  // Get contact by ID
  getContact: async (contactId) => {
    const response = await api.get(`/api/contacts/${contactId}`);
    return response.data;
  },

  // Export contacts
  exportContacts: async (filters = {}) => {
    const response = await api.post('/api/contacts/export', filters);
    return response.data;
  },
};
