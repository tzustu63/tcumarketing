import React, { useState, useEffect, useMemo } from 'react';
import { countries, countryCities, countryKeywords, getAllKeywords } from '../config/formOptions';
import api from '../services/api';
import { debounce } from '../utils/debounce';

const ContactFilters = ({ filters, onFilterChange }) => {
  const [localFilters, setLocalFilters] = useState(filters);
  const [historicalKeywords, setHistoricalKeywords] = useState([]);
  const [historicalCities, setHistoricalCities] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Update local filters when props change (e.g., from navigation)
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  // Load historical keywords and cities from API
  const loadHistory = async (countryCode) => {
    if (!countryCode) {
      setHistoricalKeywords([]);
      setHistoricalCities([]);
      return;
    }
    
    setLoadingHistory(true);
    try {
      const [keywordsRes, citiesRes] = await Promise.all([
        api.get(`/api/keywords/history?country=${countryCode}`),
        api.get(`/api/keywords/cities/history?country=${countryCode}`)
      ]);
      
      setHistoricalKeywords(keywordsRes.data.keywords || []);
      setHistoricalCities(citiesRes.data.cities || []);
    } catch (err) {
      console.error('載入歷史記錄失敗:', err);
      setHistoricalKeywords([]);
      setHistoricalCities([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  // Load history when country changes
  useEffect(() => {
    if (localFilters.country) {
      loadHistory(localFilters.country);
    } else {
      setHistoricalKeywords([]);
      setHistoricalCities([]);
    }
  }, [localFilters.country]);

  // Get keywords based on selected country (combine static and historical)
  const getAvailableKeywords = () => {
    if (!localFilters.country) {
      // If no country selected, show all keywords from all countries
      return getAllKeywords();
    }
    const staticKeywords = countryKeywords[localFilters.country] || [];
    const historical = historicalKeywords.filter(k => !staticKeywords.includes(k));
    return [...staticKeywords, ...historical];
  };

  // Get cities based on selected country (combine static and historical)
  const getAvailableCities = () => {
    if (!localFilters.country) {
      // If no country selected, show all cities from all countries
      const allCities = Object.values(countryCities).flat();
      return [...new Set(allCities)].sort();
    }
    const staticCities = countryCities[localFilters.country] || [];
    const historical = historicalCities.filter(c => !staticCities.includes(c));
    return [...staticCities, ...historical];
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setLocalFilters(prev => {
      const newFilters = { ...prev, [name]: value };
      // Reset keyword and city when country changes
      if (name === 'country') {
        newFilters.keyword = '';
        newFilters.city = '';
        loadHistory(value);
      }
      return newFilters;
    });
  };

  // Note: Debouncing not needed here as filters are applied via button click
  // If real-time search is needed in future, uncomment this:
  // const debouncedApplyFilters = useMemo(
  //   () => debounce((filters) => {
  //     onFilterChange(filters);
  //   }, 500),
  //   [onFilterChange]
  // );

  const handleApply = () => {
    onFilterChange(localFilters);
  };

  const handleReset = () => {
    const resetFilters = {
      country: '',
      keyword: '',
      institution_type: '',
      city: '',
    };
    setLocalFilters(resetFilters);
    onFilterChange(resetFilters);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">篩選條件</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            國家
          </label>
          <select
            name="country"
            value={localFilters.country || ''}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部國家</option>
            {countries.map(country => (
              <option key={country.code} value={country.code}>{country.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            搜尋關鍵字
          </label>
          <select
            name="keyword"
            value={localFilters.keyword || ''}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部關鍵字</option>
            {getAvailableKeywords().map(keyword => (
              <option key={keyword} value={keyword}>{keyword}</option>
            ))}
          </select>
          {loadingHistory ? (
            <div className="mt-1 text-xs text-gray-500">
              載入歷史關鍵字中...
            </div>
          ) : localFilters.country ? (
            <div className="mt-1 text-xs text-gray-500">
              已載入 {getAvailableKeywords().length} 個關鍵字（包含 {countryKeywords[localFilters.country]?.length || 0} 個預設 + {historicalKeywords.length} 個歷史）
            </div>
          ) : (
            <div className="mt-1 text-xs text-gray-500">
              顯示所有國家的關鍵字
            </div>
          )}
          {/* Show historical keywords that can be deleted */}
          {localFilters.country && historicalKeywords.length > 0 && (
            <div className="mt-2">
              <div className="text-xs text-gray-600 mb-1">歷史關鍵字（可刪除）：</div>
              <div className="flex flex-wrap gap-2">
                {historicalKeywords.filter(k => !countryKeywords[localFilters.country]?.includes(k)).map(keyword => (
                  <span
                    key={keyword}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
                  >
                    {keyword}
                    <button
                      type="button"
                      onClick={async () => {
                        try {
                          await api.delete(`/api/keywords/delete?country=${localFilters.country}&keyword=${encodeURIComponent(keyword)}`);
                          await loadHistory(localFilters.country);
                          // Clear filter if it matches
                          if (localFilters.keyword === keyword) {
                            setLocalFilters(prev => ({ ...prev, keyword: '' }));
                          }
                        } catch (err) {
                          console.error('刪除關鍵字失敗:', err);
                          alert('刪除關鍵字失敗: ' + (err.response?.data?.detail || err.message));
                        }
                      }}
                      className="ml-1 text-blue-600 hover:text-blue-800"
                      title="刪除此關鍵字"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            城市
          </label>
          <select
            name="city"
            value={localFilters.city}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部城市</option>
            {getAvailableCities().map(city => (
              <option key={city} value={city}>{city}</option>
            ))}
          </select>
          {loadingHistory ? (
            <div className="mt-1 text-xs text-gray-500">
              載入歷史城市中...
            </div>
          ) : localFilters.country ? (
            <div className="mt-1 text-xs text-gray-500">
              已載入 {getAvailableCities().length} 個城市（包含 {countryCities[localFilters.country]?.length || 0} 個預設 + {historicalCities.length} 個歷史）
            </div>
          ) : (
            <div className="mt-1 text-xs text-gray-500">
              顯示所有城市
            </div>
          )}
          {/* Show historical cities that can be deleted */}
          {localFilters.country && historicalCities.length > 0 && (
            <div className="mt-2">
              <div className="text-xs text-gray-600 mb-1">歷史城市（可刪除）：</div>
              <div className="flex flex-wrap gap-2">
                {historicalCities.filter(c => !countryCities[localFilters.country]?.includes(c)).map(city => (
                  <span
                    key={city}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
                  >
                    {city}
                    <button
                      type="button"
                      onClick={async () => {
                        try {
                          await api.delete(`/api/keywords/cities/delete?country=${localFilters.country}&city=${encodeURIComponent(city)}`);
                          await loadHistory(localFilters.country);
                          // Clear filter if it matches
                          if (localFilters.city === city) {
                            setLocalFilters(prev => ({ ...prev, city: '' }));
                          }
                        } catch (err) {
                          console.error('刪除城市失敗:', err);
                          alert('刪除城市失敗: ' + (err.response?.data?.detail || err.message));
                        }
                      }}
                      className="ml-1 text-blue-600 hover:text-blue-800"
                      title="刪除此城市"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-end space-x-3 mt-4">
        <button
          onClick={handleReset}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
        >
          重置
        </button>
        <button
          onClick={handleApply}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          套用篩選
        </button>
      </div>
    </div>
  );
};

export default ContactFilters;
