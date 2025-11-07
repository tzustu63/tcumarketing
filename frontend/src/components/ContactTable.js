import React, { useMemo, useCallback } from 'react';
import { countries, countryCities } from '../config/formOptions';

const ContactTable = React.memo(({ contacts }) => {
  // Memoize country map for O(1) lookup instead of O(n) find
  const countryMap = useMemo(() => {
    const map = new Map();
    countries.forEach(c => map.set(c.code, c.name));
    return map;
  }, []);

  // Memoize city maps for each country
  const cityMaps = useMemo(() => {
    const maps = new Map();
    Object.keys(countryCities).forEach(countryCode => {
      const citySet = new Set(countryCities[countryCode]);
      maps.set(countryCode, citySet);
    });
    return maps;
  }, []);

  const formatDate = useCallback((dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('zh-TW');
  }, []);

  const getQualityColor = useCallback((score) => {
    if (!score) return 'text-gray-500';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  }, []);

  const getCountryName = useCallback((countryCode) => {
    return countryMap.get(countryCode) || countryCode || 'ID';
  }, [countryMap]);

  const getCityName = useCallback((cityName, countryCode) => {
    if (!cityName) return '-';
    // City validation is not needed for display, just return the name
    return cityName;
  }, []);

  if (contacts.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-12 text-center">
        <p className="text-gray-500">無符合條件的聯絡資訊</p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                國家
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                城市
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                機構名稱
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                關鍵字
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                WhatsApp
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                來源
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                品質分數
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                萃取日期
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {contacts.map((contact) => (
              <tr key={contact.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <span className="font-medium">{getCountryName(contact.country)}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {getCityName(contact.city, contact.country)}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  <div className="max-w-xs truncate" title={contact.institution_name}>
                    {contact.institution_name}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {contact.keyword || '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  {contact.email ? (
                    <a
                      href={`mailto:${contact.email}`}
                      className="text-blue-600 hover:text-blue-800 truncate block max-w-xs"
                      title={contact.email}
                    >
                      {contact.email}
                    </a>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {contact.whatsapp ? (
                    <a
                      href={`https://wa.me/${contact.whatsapp.replace(/[^0-9]/g, '')}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-green-600 hover:text-green-800"
                    >
                      {contact.whatsapp}
                    </a>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  <div className="flex flex-col">
                    <span className="text-xs text-gray-400 uppercase">
                      {contact.source_platform}
                    </span>
                    <a
                      href={contact.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 truncate max-w-xs"
                      title={contact.source_url}
                    >
                      連結
                    </a>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={`font-medium ${getQualityColor(contact.quality_score)}`}>
                    {contact.quality_score ? contact.quality_score.toFixed(0) : '-'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(contact.extracted_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
});

ContactTable.displayName = 'ContactTable';

export default ContactTable;
