/**
 * Shared form options for countries, cities, and keywords
 * Used in both TaskForm and ContactFilters
 */

export const countries = [
  { code: 'ID', name: '印尼 (Indonesia)', domain: 'google.co.id' },
  { code: 'MY', name: '馬來西亞 (Malaysia)', domain: 'google.com.my' },
  { code: 'SG', name: '新加坡 (Singapore)', domain: 'google.com.sg' },
  { code: 'TH', name: '泰國 (Thailand)', domain: 'google.co.th' },
  { code: 'VN', name: '越南 (Vietnam)', domain: 'google.com.vn' },
  { code: 'PH', name: '菲律賓 (Philippines)', domain: 'google.com.ph' },
  { code: 'MM', name: '緬甸 (Myanmar)', domain: 'google.com.mm' },
  { code: 'KH', name: '柬埔寨 (Cambodia)', domain: 'google.com.kh' },
  { code: 'IN', name: '印度 (India)', domain: 'google.co.in' },
  { code: 'HK', name: '香港 (Hong Kong)', domain: 'google.com.hk' },
  { code: 'MO', name: '澳門 (Macau)', domain: 'google.com.mo' },
];

export const countryKeywords = {
  'ID': [
    'University',
    'College',
    'Sekolah Internasional',
    'Pusat Bahasa Mandarin',
    'Agen Pendidikan',
    'Konsultan Pendidikan',
    'Bimbingan Belajar',
    'Sekolah Kejuruan',
    'International School',
    'Language Center',
    'Study Abroad Consultant',
  ],
  'MY': [
    'University',
    'College',
    'International School',
    '獨立中學',
    '華文中學',
    '語言中心',
    '補習中心',
    '留學代辦',
    'Sekolah Antarabangsa',
    'Pusat Bahasa',
    'Tuition Centre',
  ],
  'SG': [
    'University',
    'College',
    'International School',
    '國際學校',
    'Language School',
    '語言學校',
    'Chinese Language Centre',
    '華文補習',
    'Tuition Centre',
    '補習中心',
    'Education Consultancy',
    '留學諮詢',
  ],
  'TH': [
    'University',
    'College',
    'International School',
    'โรงเรียนนานาชาติ',
    'Language School',
    'ศูนย์ภาษา',
    'Chinese Language Center',
    'ศูนย์ภาษาจีน',
    'Study Abroad Consultant',
    'ที่ปรึกษาการศึกษา',
  ],
  'VN': [
    'University',
    'College',
    'International School',
    'Trường Quốc Tế',
    'Language Center',
    'Trung Tâm Ngoại Ngữ',
    'Chinese Language School',
    'Trung Tâm Tiếng Trung',
    'Study Abroad Agency',
    'Tư Vấn Du Học',
  ],
  'PH': [
    'University',
    'College',
    'International School',
    'Language School',
    'Chinese School',
    'Study Abroad Consultant',
    'Tutorial Center',
    'Review Center',
    'Education Agency',
  ],
  'MM': [
    'University',
    'College',
    'International School',
    'Language Center',
    'Chinese Language School',
    'Education Consultant',
    'Tutorial School',
  ],
  'KH': [
    'University',
    'College',
    'International School',
    'Language School',
    'Chinese Language Center',
    'Study Abroad Agency',
    'Tutorial Center',
  ],
  'IN': [
    'University',
    'College',
    'International School',
    'Language Institute',
    'Chinese Language Academy',
    'Study Abroad Consultancy',
    'Coaching Centre',
    'Tutorial Classes',
  ],
  'HK': [
    'University',
    'College',
    '國際學校',
    '語言中心',
    '普通話中心',
    '留學顧問',
    '補習社',
    '教育中心',
    '升學顧問',
    'International School',
    'Language Centre',
    'Tutorial Centre',
  ],
  'MO': [
    'University',
    'College',
    '國際學校',
    '語言中心',
    '普通話學校',
    '留學中心',
    '補習中心',
    '教育顧問',
    'International School',
    'Language Center',
  ],
};

export const countryCities = {
  'ID': [
    'Jakarta', 'Surabaya', 'Bandung', 'Bekasi', 'Medan', 'Tangerang', 'Depok', 'Semarang',
    'Palembang', 'Makassar', 'South Tangerang', 'Batam', 'Bogor', 'Pekanbaru', 'Bandar Lampung',
    'Padang', 'Malang', 'Denpasar', 'Samarinda', 'Tasikmalaya', 'Banjarmasin', 'Pontianak',
    'Cimahi', 'Balikpapan', 'Jambi', 'Surakarta', 'Serang', 'Manado', 'Mataram', 'Yogyakarta'
  ],
  'MY': [
    'Kuala Lumpur', 'Seberang Perai', 'Kajang', 'Klang', 'Subang Jaya', 'Johor Bahru', 'Ipoh',
    'Shah Alam', 'Petaling Jaya', 'Kuching', 'Kota Kinabalu', 'Sandakan', 'Seremban', 'Iskandar Puteri',
    'Kuantan', 'Malacca City', 'Kota Bharu', 'Alor Setar', 'Tawau', 'George Town', 'Kuala Terengganu',
    'Sungai Petani', 'Miri', 'Taiping', 'Sibu', 'Kulim', 'Batu Pahat', 'Kangar', 'Putrajaya', 'Labuan'
  ],
  'SG': [
    'Bedok', 'Tampines', 'Jurong West', 'Woodlands', 'Hougang', 'Yishun', 'Sengkang', 'Choa Chu Kang',
    'Punggol', 'Ang Mo Kio', 'Bukit Batok', 'Bukit Panjang', 'Pasir Ris', 'Sembawang', 'Queenstown',
    'Toa Payoh', 'Clementi', 'Geylang', 'Kallang', 'Serangoon', 'Bishan', 'Marine Parade', 'Bukit Merah',
    'Central Area', 'Novena', 'Orchard', 'Jurong East', 'Changi', 'Sentosa', 'Paya Lebar'
  ],
  'TH': [
    'Bangkok', 'Samut Prakan', 'Nonthaburi', 'Chiang Mai', 'Hat Yai', 'Pak Kret', 'Si Racha', 'Phuket',
    'Khon Kaen', 'Udon Thani', 'Nakhon Ratchasima', 'Surat Thani', 'Chon Buri', 'Nakhon Si Thammarat',
    'Rayong', 'Lampang', 'Chiang Rai', 'Ubon Ratchathani', 'Pattaya', 'Nakhon Pathom', 'Saraburi',
    'Phitsanulok', 'Krabi', 'Hua Hin', 'Ayutthaya', 'Songkhla', 'Samut Sakhon', 'Ratchaburi', 'Trang', 'Yala'
  ],
  'VN': [
    'Ho Chi Minh City', 'Hanoi', 'Hai Phong', 'Da Nang', 'Bien Hoa', 'Can Tho', 'Vung Tau', 'Nha Trang',
    'Hue', 'Buon Ma Thuot', 'Nam Dinh', 'Quy Nhon', 'Thai Nguyen', 'Phan Thiet', 'Cam Ranh', 'Vinh',
    'My Tho', 'Rach Gia', 'Da Lat', 'Long Xuyen', 'Thai Binh', 'Bac Lieu', 'Bac Giang', 'Ca Mau',
    'Viet Tri', 'Ben Tre', 'Phan Rang', 'Tan An', 'Pleiku', 'Soc Trang'
  ],
  'PH': [
    'Quezon City', 'Manila', 'Caloocan', 'Davao City', 'Cebu City', 'Zamboanga City', 'Taguig', 'Antipolo',
    'Pasig', 'Cagayan de Oro', 'Parañaque', 'Dasmarinas', 'Valenzuela', 'Bacoor', 'General Santos',
    'Las Piñas', 'Makati', 'Bacolod', 'Muntinlupa', 'San Jose del Monte', 'Iloilo City', 'Marikina',
    'Pasay', 'Calamba', 'Mandaluyong', 'Baguio', 'Batangas City', 'Iligan', 'Mandaue', 'Butuan'
  ],
  'MM': [
    'Yangon', 'Mandalay', 'Naypyidaw', 'Mawlamyine', 'Bago', 'Pathein', 'Monywa', 'Sittwe', 'Meiktila',
    'Myeik', 'Taunggyi', 'Myingyan', 'Dawei', 'Pyay', 'Hinthada', 'Lashio', 'Pakokku', 'Magway',
    'Myitkyina', 'Thaton', 'Kalay', 'Loikaw', 'Sagaing', 'Taungoo', 'Hpa-An', 'Kyaukse', 'Bhamo',
    'Hakha', 'Kengtung', 'Putao'
  ],
  'KH': [
    'Phnom Penh', 'Siem Reap', 'Battambang', 'Sihanoukville', 'Kampong Cham', 'Prey Veng', 'Ta Khmau',
    'Kampong Speu', 'Pursat', 'Kampong Chhnang', 'Kratie', 'Kampot', 'Stung Treng', 'Koh Kong',
    'Svay Rieng', 'Takeo', 'Banlung', 'Pailin', 'Poipet', 'Sisophon'
  ],
  'IN': [
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Ahmedabad', 'Chennai', 'Kolkata', 'Surat', 'Pune',
    'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Pimpri-Chinchwad',
    'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik', 'Faridabad', 'Meerut', 'Rajkot',
    'Kalyan-Dombivali', 'Vasai-Virar', 'Varanasi'
  ],
  'HK': [
    'Sha Tin', 'Tuen Mun', 'Yuen Long', 'Tsuen Wan', 'Kwun Tong', 'Tai Po', 'Sai Kung', 'Tseung Kwan O',
    'Tsing Yi', 'Fanling', 'Sheung Shui', 'Ma On Shan', 'Tin Shui Wai', 'Tung Chung', 'Central', 'Causeway Bay',
    'Mong Kok', 'Tsim Sha Tsui', 'Wan Chai', 'Kowloon City', 'Sham Shui Po', 'Wong Tai Sin', 'Yau Ma Tei',
    'Jordan', 'Admiralty', 'Quarry Bay', 'North Point', 'Chai Wan', 'Aberdeen', 'Stanley'
  ],
  'MO': [
    'Macau Peninsula', 'Taipa', 'Cotai', 'Coloane', 'NAPE', 'Areia Preta', 'Fai Chi Kei', 'Horta e Costa',
    'Nossa Senhora de Fátima', 'Santo António', 'São Lázaro', 'Sé', 'São Lourenço', 'Nossa Senhora do Carmo'
  ],
};

// Get all unique keywords from all countries
export const getAllKeywords = () => {
  const allKeywords = new Set();
  Object.values(countryKeywords).forEach(keywords => {
    keywords.forEach(keyword => allKeywords.add(keyword));
  });
  return Array.from(allKeywords).sort();
};

// Get all unique cities from all countries
export const getAllCities = () => {
  const allCities = new Set();
  Object.values(countryCities).forEach(cities => {
    cities.forEach(city => allCities.add(city));
  });
  return Array.from(allCities).sort();
};
