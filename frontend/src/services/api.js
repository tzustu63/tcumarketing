import axios from "axios";

// 動態獲取 API URL：優先使用環境變數，否則根據當前頁面自動推斷
const getApiBaseURL = () => {
  // 如果有環境變數且不是 localhost，直接使用
  if (
    process.env.REACT_APP_API_URL &&
    process.env.REACT_APP_API_URL.trim() !== ""
  ) {
    return process.env.REACT_APP_API_URL;
  }

  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  const port = window.location.port;

  if (hostname === "localhost" || hostname === "127.0.0.1") {
    const apiPort = port === "3000" || port === "" ? "8000" : port;
    return `${protocol}//${hostname}:${apiPort}`;
  }

  return `${protocol}//${hostname}`;
};

const API_BASE_URL = getApiBaseURL();

const safeTransformResponse = (data, headers) => {
  if (data == null || typeof data !== "string") {
    return data;
  }

  const trimmed = data.trim();
  if (!trimmed) {
    return trimmed;
  }

  const contentType = (headers?.["content-type"] || "").toLowerCase();
  const looksLikeJson =
    contentType.includes("application/json") ||
    contentType.includes("+json") ||
    trimmed.startsWith("{") ||
    trimmed.startsWith("[");

  if (!looksLikeJson) {
    return trimmed;
  }

  try {
    return JSON.parse(trimmed);
  } catch (parseError) {
    console.warn("JSON 解析失敗，回傳原始字串以便後續處理", {
      preview: trimmed.slice(0, 200),
    });
    return trimmed;
  }
};

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 秒超時（針對任務創建等耗時操作）
  headers: {
    "Content-Type": "application/json",
  },
  transformResponse: [safeTransformResponse],
  transitional: {
    forcedJSONParsing: false,
    silentJSONParsing: true,
  },
});

console.log('API Base URL:', API_BASE_URL);

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      console.error("API Error:", error.response.data);
    } else if (error.code === 'ECONNABORTED') {
      // 處理超時錯誤
      console.error("請求超時，請檢查網路連接或稍後再試");
      error.message = "請求超時，請檢查網路連接或稍後再試";
    } else if (error.request) {
      // 請求已發出但沒有收到響應
      console.error("無法連接到伺服器，請檢查網路連接");
      error.message = "無法連接到伺服器，請檢查網路連接";
    }
    return Promise.reject(error);
  }
);

export default api;
