import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { countries, countryCities, countryKeywords } from '../config/formOptions';

const TaskForm = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    keyword: '',
    city: '',
    country: 'ID',
    target_platforms: ['website'],
    max_results: 100,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [historicalKeywords, setHistoricalKeywords] = useState([]);
  const [historicalCities, setHistoricalCities] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [keywordToDelete, setKeywordToDelete] = useState(null);
  const [cityToDelete, setCityToDelete] = useState(null);
  
  // Use unified configuration from formOptions.js
  // countryKeywords, countryCities, and countries are now imported
  
  // Custom keywords and cities management
  const [customKeywords, setCustomKeywords] = useState([]);
  const [customCities, setCustomCities] = useState([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [newCity, setNewCity] = useState('');
  const [showKeywordInput, setShowKeywordInput] = useState(false);
  const [showCityInput, setShowCityInput] = useState(false);

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

  // Load history on component mount and when country changes
  useEffect(() => {
    if (formData.country) {
      loadHistory(formData.country);
    }
  }, [formData.country]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // When country changes, reset keyword and city and load history
    if (name === 'country') {
      setCustomKeywords([]);
      setCustomCities([]);
      setFormData(prev => ({ ...prev, keyword: '', city: '' }));
      loadHistory(value);
    }
  };
  
  // Get keywords for selected country (combine static, historical, and custom)
  const getAvailableKeywords = () => {
    const countrySpecific = countryKeywords[formData.country] || [];
    const historical = historicalKeywords.filter(k => 
      !countrySpecific.includes(k) && !customKeywords.includes(k)
    );
    return [...countrySpecific, ...historical, ...customKeywords];
  };
  
  // Get cities for selected country (combine static, historical, and custom)
  const getAvailableCities = () => {
    const countrySpecific = countryCities[formData.country] || [];
    const historical = historicalCities.filter(c => 
      !countrySpecific.includes(c) && !customCities.includes(c)
    );
    return [...countrySpecific, ...historical, ...customCities];
  };



  const handleAddKeyword = async () => {
    const keyword = newKeyword.trim();
    if (!keyword) return;
    
    // Only check if it's in the static list (predefined keywords)
    const staticKeywords = countryKeywords[formData.country] || [];
    if (staticKeywords.includes(keyword)) {
      setError('此關鍵字已在預設列表中，無需新增');
      return;
    }
    
    setError(null); // Clear previous errors
    
    try {
      // Save to API - let backend decide if it exists
      const response = await api.post(`/api/keywords/add?country=${formData.country}&keyword=${encodeURIComponent(keyword)}`);
      
      // Check API response message
      if (response.data.message === '關鍵字已存在') {
        // Keyword already exists in stored_keywords, but that's okay
        // Just reload history to get updated list
        await loadHistory(formData.country);
        setNewKeyword('');
        setShowKeywordInput(false);
        setError(null);
        return;
      }
      
      // Keyword was successfully added or restored
      // Reload history to get updated list
      await loadHistory(formData.country);
      
      // Also add to custom keywords for immediate use
      setCustomKeywords([...customKeywords, keyword]);
      setNewKeyword('');
      setShowKeywordInput(false);
      setError(null);
    } catch (err) {
      console.error('新增關鍵字失敗:', err);
      // Show detailed error message from API
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || '新增關鍵字失敗';
      setError(errorMessage);
    }
  };

  const handleDeleteKeyword = async (keyword) => {
    // Check if it's a historical keyword (not in static list)
    const countrySpecific = countryKeywords[formData.country] || [];
    const isHistorical = historicalKeywords.includes(keyword) && !countrySpecific.includes(keyword);
    
    if (isHistorical) {
      // Delete from API with confirmation
      try {
        await api.delete(`/api/keywords/delete?country=${formData.country}&keyword=${encodeURIComponent(keyword)}`);
        // Reload history
        await loadHistory(formData.country);
        setError(null);
      } catch (err) {
        console.error('刪除關鍵字失敗:', err);
        setError(err.response?.data?.detail || '刪除關鍵字失敗');
        return;
      }
    } else {
      // Remove from custom keywords
      setCustomKeywords(customKeywords.filter(k => k !== keyword));
    }
    
    // Clear form field if it matches
    if (formData.keyword === keyword) {
      setFormData(prev => ({ ...prev, keyword: '' }));
    }
    
    // Clear delete confirmation
    setKeywordToDelete(null);
  };

  const confirmDeleteKeyword = (keyword) => {
    setKeywordToDelete(keyword);
  };

  const cancelDeleteKeyword = () => {
    setKeywordToDelete(null);
  };

  const handleAddCity = async () => {
    const city = newCity.trim();
    if (!city) return;
    
    // Only check if it's in the static list (predefined cities)
    const staticCities = countryCities[formData.country] || [];
    if (staticCities.includes(city)) {
      setError('此城市已在預設列表中，無需新增');
      return;
    }
    
    setError(null); // Clear previous errors
    
    try {
      // Save to API - let backend decide if it exists
      const response = await api.post(`/api/keywords/cities/add?country=${formData.country}&city=${encodeURIComponent(city)}`);
      
      // Check API response message
      if (response.data.message === '城市已存在') {
        // City already exists in stored_keywords, but that's okay
        // Just reload history to get updated list
        await loadHistory(formData.country);
        setNewCity('');
        setShowCityInput(false);
        setError(null);
        return;
      }
      
      // City was successfully added or restored
      // Reload history to get updated list
      await loadHistory(formData.country);
      
      // Also add to custom cities for immediate use
      setCustomCities([...customCities, city]);
      setNewCity('');
      setShowCityInput(false);
      setError(null);
    } catch (err) {
      console.error('新增城市失敗:', err);
      // Show detailed error message from API
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || '新增城市失敗';
      setError(errorMessage);
    }
  };

  const handleDeleteCity = async (city) => {
    // Check if it's a historical city (not in static list)
    const countrySpecific = countryCities[formData.country] || [];
    const isHistorical = historicalCities.includes(city) && !countrySpecific.includes(city);
    
    if (isHistorical) {
      // Delete from API with confirmation
      try {
        await api.delete(`/api/keywords/cities/delete?country=${formData.country}&city=${encodeURIComponent(city)}`);
        // Reload history
        await loadHistory(formData.country);
        setError(null);
      } catch (err) {
        console.error('刪除城市失敗:', err);
        setError(err.response?.data?.detail || '刪除城市失敗');
        return;
      }
    } else {
      // Remove from custom cities
      setCustomCities(customCities.filter(c => c !== city));
    }
    
    // Clear form field if it matches
    if (formData.city === city) {
      setFormData(prev => ({ ...prev, city: '' }));
    }
    
    // Clear delete confirmation
    setCityToDelete(null);
  };

  const confirmDeleteCity = (city) => {
    setCityToDelete(city);
  };

  const cancelDeleteCity = () => {
    setCityToDelete(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.keyword || !formData.city) {
      setError('請填寫所有必填欄位');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await onSubmit(formData);
    } catch (err) {
      setError(err.response?.data?.detail || '建立任務失敗');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">建立新任務</h3>
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            國家 *
          </label>
          <select
            name="country"
            value={formData.country}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            {countries.map(country => (
              <option key={country.code} value={country.code}>
                {country.name} ({country.domain})
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="block text-sm font-medium text-gray-700">
              搜尋關鍵字 *
            </label>
            <button
              type="button"
              onClick={() => setShowKeywordInput(!showKeywordInput)}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              {showKeywordInput ? '取消' : '+ 新增關鍵字'}
            </button>
          </div>
          
          {showKeywordInput && (
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddKeyword())}
                placeholder="輸入新關鍵字"
                className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={handleAddKeyword}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                新增
              </button>
            </div>
          )}
          
          <select
            name="keyword"
            value={formData.keyword}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">請選擇關鍵字</option>
            {getAvailableKeywords().map(keyword => (
              <option key={keyword} value={keyword}>{keyword}</option>
            ))}
          </select>
          
          <div className="mt-2 text-xs text-gray-500">
            {loadingHistory ? (
              '載入歷史關鍵字中...'
            ) : countryKeywords[formData.country] ? (
              `已載入 ${getAvailableKeywords().length} 個關鍵字（包含 ${countryKeywords[formData.country].length} 個預設 + ${historicalKeywords.length} 個歷史）`
            ) : (
              '請先選擇國家以載入關鍵字'
            )}
          </div>
          
          {/* Show historical keywords that can be deleted */}
          {historicalKeywords.length > 0 && (
            <div className="mt-2">
              <div className="text-xs text-gray-600 mb-1">歷史關鍵字（可刪除）：</div>
              <div className="flex flex-wrap gap-2">
                {historicalKeywords.filter(k => !countryKeywords[formData.country]?.includes(k)).map(keyword => (
                  <span
                    key={keyword}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    {keyword}
                    <button
                      type="button"
                      onClick={() => confirmDeleteKeyword(keyword)}
                      className="ml-2 text-blue-600 hover:text-red-600 font-bold"
                      title="刪除此關鍵字"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Show custom keywords (session only) */}
          {customKeywords.length > 0 && (
            <div className="mt-2">
              <div className="text-xs text-gray-600 mb-1">本階段新增的關鍵字：</div>
              <div className="flex flex-wrap gap-2">
                {customKeywords.map(keyword => (
                  <span
                    key={keyword}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-purple-100 text-purple-800"
                  >
                    {keyword}
                    <button
                      type="button"
                      onClick={() => handleDeleteKeyword(keyword)}
                      className="ml-2 text-purple-600 hover:text-purple-800"
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
          <div className="flex justify-between items-center mb-1">
            <label className="block text-sm font-medium text-gray-700">
              城市 *
            </label>
            <button
              type="button"
              onClick={() => setShowCityInput(!showCityInput)}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              {showCityInput ? '取消' : '+ 新增城市'}
            </button>
          </div>
          
          {showCityInput && (
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newCity}
                onChange={(e) => setNewCity(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddCity())}
                placeholder="輸入新城市"
                className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={handleAddCity}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                新增
              </button>
            </div>
          )}
          
          <select
            name="city"
            value={formData.city}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">請選擇城市</option>
            {getAvailableCities().map(city => (
              <option key={city} value={city}>{city}</option>
            ))}
          </select>
          
          <div className="mt-2 text-xs text-gray-500">
            {loadingHistory ? (
              '載入歷史城市中...'
            ) : countryCities[formData.country] ? (
              `已載入 ${getAvailableCities().length} 個城市（包含 ${countryCities[formData.country].length} 個預設 + ${historicalCities.length} 個歷史）`
            ) : (
              '請先選擇國家以載入城市'
            )}
          </div>
          
          {/* Show historical cities that can be deleted */}
          {historicalCities.length > 0 && (
            <div className="mt-2">
              <div className="text-xs text-gray-600 mb-1">歷史城市（可刪除）：</div>
              <div className="flex flex-wrap gap-2">
                {historicalCities.filter(c => !countryCities[formData.country]?.includes(c)).map(city => (
                  <span
                    key={city}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    {city}
                    <button
                      type="button"
                      onClick={() => confirmDeleteCity(city)}
                      className="ml-2 text-blue-600 hover:text-red-600 font-bold"
                      title="刪除此城市"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Show custom cities (session only) */}
          {customCities.length > 0 && (
            <div className="mt-2">
              <div className="text-xs text-gray-600 mb-1">本階段新增的城市：</div>
              <div className="flex flex-wrap gap-2">
                {customCities.map(city => (
                  <span
                    key={city}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800"
                  >
                    {city}
                    <button
                      type="button"
                      onClick={() => handleDeleteCity(city)}
                      className="ml-2 text-green-600 hover:text-green-800"
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
            最大結果數
          </label>
          <input
            type="number"
            name="max_results"
            value={formData.max_results}
            onChange={handleChange}
            min="10"
            max="500"
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex justify-end space-x-3 pt-4">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            disabled={submitting}
          >
            取消
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            disabled={submitting}
          >
            {submitting ? '建立中...' : '建立任務'}
          </button>
        </div>
      </form>

      {/* Delete Confirmation Modal for Keyword */}
      {keywordToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">確認刪除關鍵字</h3>
            <p className="text-gray-600 mb-6">
              確定要刪除關鍵字「<span className="font-semibold">{keywordToDelete}</span>」嗎？此操作無法復原。
            </p>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={cancelDeleteKeyword}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                取消
              </button>
              <button
                type="button"
                onClick={() => handleDeleteKeyword(keywordToDelete)}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                確認刪除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal for City */}
      {cityToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">確認刪除城市</h3>
            <p className="text-gray-600 mb-6">
              確定要刪除城市「<span className="font-semibold">{cityToDelete}</span>」嗎？此操作無法復原。
            </p>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={cancelDeleteCity}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                取消
              </button>
              <button
                type="button"
                onClick={() => handleDeleteCity(cityToDelete)}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                確認刪除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskForm;
