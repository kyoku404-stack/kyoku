import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import { CONFIG } from '@/constants/config';
import type { ApiErrorResponse } from '@/types/api';

/**
 * Standardized Axios HTTP client for KEEP Enterprise Platform.
 * Configured with base URL, authentication interceptor, and structured error handling.
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: CONFIG.API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Request Interceptor: Inject JWT token if available
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('keep_auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: unknown) => Promise.reject(error)
);

// Response Interceptor: Standardize API error payloads
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorResponse>) => {
    if (error.response?.status === 401) {
      // Clear expired credentials and notify listeners
      localStorage.removeItem('keep_auth_token');
    }

    const errorPayload: ApiErrorResponse = {
      error: error.response?.data?.error || error.name || 'ApiError',
      message: error.response?.data?.message || error.message || 'An unexpected API error occurred.',
      detail: error.response?.data?.detail || null,
    };

    return Promise.reject(errorPayload);
  }
);

export default apiClient;
