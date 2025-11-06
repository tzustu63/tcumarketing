import axios from "axios";

// 動態獲取 API URL：優先使用環境變數，否則根據當前頁面自動推斷
const getApiBaseURL = () => {
  // 如果有環境變數且不是 localhost，直接使用
  if (
    process.env.REACT_APP_API_URL &&
    !process.env.REACT_APP_API_URL.includes("localhost")
  ) {
    return process.env.REACT_APP_API_URL;
  }

  // 否則根據當前頁面的 host 和 port 構建 API URL
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  const port =
    window.location.port === "3000" ? "8000" : window.location.port || "";

  // 如果端口是 3000，改為 8000（API 端口）
  if (port === "3000" || !port) {
    return `${protocol}//${hostname}:8000`;
  }

  // 否則保持相同主機，但嘗試使用 8000 端口
  return `${protocol}//${hostname}:8000`;
};

const API_BASE_URL = getApiBaseURL();

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 秒超時
  headers: {
    "Content-Type": "application/json",
  },
});

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
    }
    return Promise.reject(error);
  }
);

export default api;
