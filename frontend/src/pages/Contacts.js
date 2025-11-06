import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { contactService } from '../services/contactService';
import ContactFilters from '../components/ContactFilters';
import ContactTable from '../components/ContactTable';
import Pagination from '../components/Pagination';

const Contacts = () => {
  const location = useLocation();
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Initialize filters from navigation state if available
  const initialFilters = useMemo(() => 
    location.state?.filters || {
      country: '',
      keyword: '',
      institution_type: '',
      city: '',
    },
    [location.state]
  );
  
  const [filters, setFilters] = useState(initialFilters);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
  });

  const fetchContacts = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        ...filters,
        skip: (pagination.page - 1) * pagination.limit,
        limit: pagination.limit,
      };
      
      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (params[key] === '') delete params[key];
      });

      const data = await contactService.getContacts(params);
      
      if (Array.isArray(data)) {
        setContacts(data);
        setPagination(prev => ({ ...prev, total: data.length }));
      } else if (data.contacts) {
        setContacts(data.contacts);
        setPagination(prev => ({ ...prev, total: data.total || data.contacts.length }));
      } else if (data.items) {
        setContacts(data.items);
        setPagination(prev => ({ ...prev, total: data.total || data.items.length }));
      } else {
        setContacts([]);
      }
    } catch (err) {
      console.error('載入聯絡資訊失敗:', err);
      setContacts([]);
    } finally {
      setLoading(false);
    }
  }, [filters, pagination.page, pagination.limit]);

  useEffect(() => {
    fetchContacts();
  }, [fetchContacts]);

  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, page: 1 }));
  }, []);

  const handlePageChange = useCallback((newPage) => {
    setPagination(prev => ({ ...prev, page: newPage }));
  }, []);

  const totalPages = Math.ceil(pagination.total / pagination.limit);

  return (
    <div className="px-4 sm:px-0">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">聯絡資訊資料庫</h2>

      <ContactFilters filters={filters} onFilterChange={handleFilterChange} />

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-2 text-gray-600">載入中...</p>
        </div>
      ) : (
        <>
          <div className="mb-4 text-sm text-gray-600">
            共 {pagination.total} 筆資料
          </div>
          
          <ContactTable contacts={contacts} />

          {totalPages > 1 && (
            <Pagination
              currentPage={pagination.page}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          )}
        </>
      )}
    </div>
  );
};

export default Contacts;
