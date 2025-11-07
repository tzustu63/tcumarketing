import React, { useState, useEffect } from 'react';
import { contactService } from '../services/contactService';
import { countries, countryCities, countryKeywords, getAllKeywords } from '../config/formOptions';
import api from '../services/api';

const Export = () => {
  const [filters, setFilters] = useState({
    country: '',
    keyword: '',
    institution_type: '',
    city: '',
  });
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [historicalKeywords, setHistoricalKeywords] = useState([]);
  const [historicalCities, setHistoricalCities] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const institutionTypes = [
    { value: '', label: '全部' },
    { value: '高中', label: '高中' },
    { value: '華語中心', label: '華語中心' },
    { value: '代辦', label: '代辦' },
  ];

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
    if (filters.country) {
      loadHistory(filters.country);
    } else {
      setHistoricalKeywords([]);
      setHistoricalCities([]);
    }
  }, [filters.country]);

  // Get keywords based on selected country (combine static and historical)
  const getAvailableKeywords = () => {
    if (!filters.country) {
      // If no country selected, show all keywords from all countries
      return getAllKeywords();
    }
    const staticKeywords = countryKeywords[filters.country] || [];
    const historical = historicalKeywords.filter(k => !staticKeywords.includes(k));
    return [...staticKeywords, ...historical];
  };

  // Get cities based on selected country (combine static and historical)
  const getAvailableCities = () => {
    if (!filters.country) {
      // If no country selected, show all cities from all countries
      const allCities = Object.values(countryCities).flat();
      return [...new Set(allCities)].sort();
    }
    const staticCities = countryCities[filters.country] || [];
    const historical = historicalCities.filter(c => !staticCities.includes(c));
    return [...staticCities, ...historical];
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => {
      const newFilters = { ...prev, [name]: value };
      // Reset keyword and city when country changes
      if (name === 'country') {
        newFilters.keyword = '';
        newFilters.city = '';
      }
      return newFilters;
    });
  };

  const handleExport = async () => {
    setExporting(true);
    setError(null);
    setSuccess(false);

    try {
      // Remove empty filters
      const exportFilters = {};
      Object.keys(filters).forEach(key => {
        if (filters[key]) exportFilters[key] = filters[key];
      });

      // Create export task
      const response = await contactService.exportContacts(exportFilters);
      const taskId = response.task_id;
      
      // Poll for task completion
      let attempts = 0;
      const maxAttempts = 60; // 60 seconds timeout
      
      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
        
        const statusResponse = await fetch(`/api/contacts/export/${taskId}/status`);
        const status = await statusResponse.json();
        
        if (status.status === 'success') {
          // Download the file using axios with blob response type
          const downloadResponse = await fetch(`/api/contacts/export/${taskId}/download`);
          
          if (!downloadResponse.ok) {
            throw new Error(`下載失敗: ${downloadResponse.statusText}`);
          }
          
          const blob = await downloadResponse.blob();
          
          // Verify blob is not empty
          if (blob.size === 0) {
            throw new Error('下載的文件為空');
          }
          
          // Create download link with proper content type
          const url = window.URL.createObjectURL(
            new Blob([blob], { 
              type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
            })
          );
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', status.filename || `contacts_export_${new Date().toISOString().split('T')[0]}.xlsx`);
          link.style.display = 'none';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          // Clean up after a short delay
          setTimeout(() => window.URL.revokeObjectURL(url), 1000);
          
          setSuccess(true);
          setTimeout(() => setSuccess(false), 5000);
          break;
        } else if (status.status === 'failure') {
          throw new Error(status.error || '匯出任務失敗');
        }
        
        attempts++;
      }
      
      if (attempts >= maxAttempts) {
        throw new Error('匯出超時，請稍後再試');
      }
    } catch (err) {
      console.error('匯出失敗:', err);
      setError(err.message || err.response?.data?.detail || '匯出失敗，請稍後再試');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="px-4 sm:px-0">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">資料匯出</h2>

      <div className="bg-white rounded-lg shadow p-6 max-w-2xl">
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">匯出說明</h3>
          <p className="text-sm text-gray-600">
            選擇篩選條件後，系統將匯出符合條件的聯絡資訊為 Excel 檔案。
            檔案包含機構名稱、類型、Email、WhatsApp、來源網址等完整資訊。
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
            匯出成功！檔案已開始下載。
          </div>
        )}

        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              國家
            </label>
            <select
              name="country"
              value={filters.country}
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
              關鍵字
            </label>
            <select
              name="keyword"
              value={filters.keyword}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loadingHistory}
            >
              <option value="">全部關鍵字</option>
              {getAvailableKeywords().map(keyword => (
                <option key={keyword} value={keyword}>{keyword}</option>
              ))}
            </select>
            {loadingHistory && (
              <p className="mt-1 text-xs text-gray-500">載入歷史關鍵字中...</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              城市
            </label>
            <select
              name="city"
              value={filters.city}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loadingHistory}
            >
              <option value="">全部城市</option>
              {getAvailableCities().map(city => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>
            {loadingHistory && (
              <p className="mt-1 text-xs text-gray-500">載入歷史城市中...</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              機構類型
            </label>
            <select
              name="institution_type"
              value={filters.institution_type}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {institutionTypes.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="border-t border-gray-200 pt-6">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {exporting ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                匯出中...
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                匯出 Excel 檔案
              </>
            )}
          </button>
        </div>

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h4 className="text-sm font-medium text-blue-800">提示</h4>
              <p className="mt-1 text-sm text-blue-700">
                匯出的檔案包含中英文雙語標題，可直接用於 Email 群發或 WhatsApp 聯繫活動。
                大量資料匯出可能需要較長時間，請耐心等待。
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Export;
