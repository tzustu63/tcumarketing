# 需求文件

## 簡介

慈濟大學招生通路自動開發系統是一個結合網頁爬蟲與自然語言處理的自動化軟體，旨在取代傳統的人工市場調查流程。系統能夠 7x24 小時不間斷地在 Google、Facebook、Instagram 上搜尋潛在合作夥伴，自動萃取聯絡資訊，並建立結構化的資料庫。系統支援多個亞洲國家和地區，包括印尼、馬來西亞、新加坡、泰國、越南、菲律賓、緬甸、柬埔寨、印度、香港和澳門，並根據每個國家的語言和教育體系提供相應的搜尋關鍵字。最終目標是大幅降低開發新通路的初期人力成本，快速擴大在亞洲市場的行銷覆蓋範圍。

## 術語表

- **System**: 慈濟大學招生通路自動開發系統
- **User**: 招生人員或招生團隊成員
- **Search Task**: 使用者定義的搜尋任務，包含國家、關鍵字、城市、目標屬性等參數
- **Target Country**: 目標國家或地區，系統支援印尼、馬來西亞、新加坡、泰國、越南、菲律賓、緬甸、柬埔寨、印度、香港和澳門
- **Country-Specific Keywords**: 根據目標國家的語言和教育體系定義的搜尋關鍵字
- **Target Institution**: 潛在合作夥伴機構（如國際學校、語言中心、留學代辦機構）
- **Contact Information**: 聯絡資訊，包含 Email 和 WhatsApp 號碼
- **Scraping Engine**: 網頁爬蟲引擎，負責模擬瀏覽器並抓取網頁內容
- **AI Extraction Module**: AI 資訊萃取模組，使用自然語言處理技術辨識聯絡資訊
- **Contact Database**: 結構化的聯絡資料庫，儲存所有萃取的資訊
- **Official Website**: 目標機構的官方網站
- **Social Media Page**: 目標機構的 Facebook 或 Instagram 頁面
- **Contact Page**: 官網上的「聯絡我們」或類似頁面
- **Google Domain**: 針對不同國家使用的 Google 搜尋域名（如 google.co.id、google.com.my）

## 需求

### 需求 1

**使用者故事：** 作為招生人員，我想要能夠定義自動化搜尋任務，以便系統能針對特定的目標市場進行資料收集

#### 驗收標準

1. THE System SHALL provide a user interface where User can input search parameters including country, keyword, city, and target platform
2. WHEN User submits a search task, THE System SHALL validate that all required parameters are provided
3. THE System SHALL support multiple countries including Indonesia, Malaysia, Singapore, Thailand, Vietnam, Philippines, Myanmar, Cambodia, India, Hong Kong, and Macau
4. WHEN User selects a country, THE System SHALL display keyword options specific to that country's language and education system
5. WHEN User selects a country, THE System SHALL display city options specific to that country
6. THE System SHALL allow User to select target platforms from Website, Facebook, and Instagram
7. THE System SHALL use the appropriate Google domain for each country when performing searches

### 需求 2

**使用者故事：** 作為招生人員，我想要系統能自動在 Google 上搜尋並抓取相關結果，以便快速找到大量潛在合作夥伴

#### 驗收標準

1. WHEN a search task is initiated, THE Scraping Engine SHALL automatically send search queries to Google with the specified parameters
2. THE Scraping Engine SHALL extract all relevant search result URLs including official websites, Facebook pages, and Instagram profiles
3. THE Scraping Engine SHALL simulate browser behavior to avoid detection and blocking
4. WHEN search results exceed one page, THE Scraping Engine SHALL automatically navigate through multiple result pages
5. THE System SHALL store all extracted URLs with their associated metadata in temporary storage for further processing

### 需求 3

**使用者故事：** 作為招生人員，我想要系統能自動從官方網站萃取聯絡資訊，以便獲得準確的 Email 和 WhatsApp 號碼

#### 驗收標準

1. WHEN an official website URL is identified, THE AI Extraction Module SHALL automatically navigate to the website
2. THE AI Extraction Module SHALL prioritize locating contact pages with keywords such as "Kontak Kami", "Hubungi Kami", or "Contact Us"
3. WHEN a contact page is found, THE AI Extraction Module SHALL extract email addresses matching Indonesian domain patterns including ".co.id", ".ac.id", and common formats
4. THE AI Extraction Module SHALL extract WhatsApp numbers matching Indonesian phone number patterns including "+62" prefix and various formatting styles
5. THE AI Extraction Module SHALL handle irregular contact information formats using natural language processing techniques

### 需求 4

**使用者故事：** 作為招生人員，我想要系統能從社群媒體頁面萃取聯絡資訊，以便擴大聯絡管道的覆蓋範圍

#### 驗收標準

1. WHEN a Facebook or Instagram page URL is identified, THE AI Extraction Module SHALL attempt to access the public "About" section
2. THE AI Extraction Module SHALL extract contact information from social media bio and description fields
3. THE System SHALL handle authentication and access restrictions for social media platforms
4. WHEN contact information is not publicly available, THE System SHALL log the page as "contact information unavailable"
5. THE AI Extraction Module SHALL identify contact information patterns specific to social media formats including "WA:", "Email:", and link-in-bio patterns

### 需求 5

**使用者故事：** 作為招生人員，我想要系統能將萃取的資訊儲存在結構化資料庫中，以便後續進行聯絡和分析

#### 驗收標準

1. WHEN contact information is successfully extracted, THE System SHALL store the data in Contact Database with all required fields
2. THE Contact Database SHALL include fields for institution name, institution type, source URL, email, WhatsApp number, and extraction date
3. THE System SHALL automatically categorize institution type based on keywords as "高中", "華語中心", or "代辦"
4. THE System SHALL prevent duplicate entries by checking existing records before insertion
5. THE System SHALL timestamp each record with the extraction date in ISO 8601 format

### 需求 6

**使用者故事：** 作為招生人員，我想要能夠匯出資料庫內容，以便用於 Email 群發或 WhatsApp 聯繫活動

#### 驗收標準

1. THE System SHALL provide an export function that allows User to download Contact Database contents
2. THE System SHALL support Excel format export with all database fields as columns
3. WHEN User requests export, THE System SHALL generate the file within 30 seconds for databases containing up to 10000 records
4. THE exported file SHALL include headers in both Chinese and English for clarity
5. THE System SHALL allow User to filter export results by institution type, city, or extraction date range

### 需求 7

**使用者故事：** 作為招生人員，我想要系統能夠 7x24 小時自動執行任務，以便持續擴充資料庫而不需人工介入

#### 驗收標準

1. THE System SHALL support background task execution without requiring User interaction
2. WHEN a search task is queued, THE System SHALL execute it automatically according to the task schedule
3. THE System SHALL provide a task queue management interface showing pending, in-progress, and completed tasks
4. THE System SHALL send notifications to User when a task is completed or encounters errors
5. THE System SHALL implement rate limiting to avoid overwhelming target websites with requests

### 需求 8

**使用者故事：** 作為招生人員，我想要系統能處理錯誤並提供清晰的日誌，以便了解系統運作狀況和排除問題

#### 驗收標準

1. WHEN the Scraping Engine encounters a blocked request, THE System SHALL implement retry logic with exponential backoff
2. WHEN extraction fails for a specific URL, THE System SHALL log the error with URL, error type, and timestamp
3. THE System SHALL provide a dashboard showing success rate, total records extracted, and error statistics
4. THE System SHALL alert User when error rate exceeds 20 percent for any given task
5. THE System SHALL maintain detailed logs for all scraping and extraction activities for at least 30 days

### 需求 9

**使用者故事：** 作為招生人員，我想要系統能支援多個國家和地區，並根據不同國家提供相應的搜尋關鍵字和城市選項，以便在不同市場進行招生

#### 驗收標準

1. THE System SHALL maintain a configuration mapping of countries to their respective search keywords
2. THE System SHALL maintain a configuration mapping of countries to their respective city lists
3. THE System SHALL maintain a configuration mapping of countries to their respective Google search domains
4. WHEN User selects a country, THE System SHALL dynamically update the keyword dropdown to show only keywords relevant to that country
5. WHEN User selects a country, THE System SHALL dynamically update the city dropdown to show only cities in that country
6. THE System SHALL support keywords in multiple languages including English, Indonesian, Malay, Thai, Vietnamese, Tagalog, Burmese, Khmer, Hindi, and Chinese
7. WHEN performing a search, THE System SHALL use the Google domain specific to the selected country
8. THE Contact Database SHALL store the country code for each contact record to enable country-based filtering
