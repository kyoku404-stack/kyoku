import axios, {
  AxiosError,
  type AxiosInstance,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios';
import { CONFIG } from '@/constants/config';
import {
  ErrorCode,
  type ApiErrorResponse,
  type ApiResponse,
} from '@/types/api';

/**
 * Custom typed error class representing an API error from the backend.
 * Encapsulates the standardized ApiErrorResponse envelope.
 */
export class ApiError extends Error {
  public readonly code: ErrorCode | string;
  public readonly status?: number;
  public readonly details?: unknown;

  constructor(
    message: string,
    code: ErrorCode | string = ErrorCode.INTERNAL_SERVER_ERROR,
    status?: number,
    details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;

    // Restore prototype chain for instanceof checks
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

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

// Request Interceptor: Inject JWT token & request tracing headers
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('keep_auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Attach request tracing ID if not already supplied
    if (config.headers && !config.headers['X-Request-ID']) {
      config.headers['X-Request-ID'] = `req_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    }

    return config;
  },
  (error: unknown) => Promise.reject(error)
);

// Response Interceptor: Standardize API error payloads to typed ApiError
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorResponse | { detail?: string }>) => {
    const status = error.response?.status;

    if (status === 401) {
      // Clear expired credentials
      localStorage.removeItem('keep_auth_token');
    }

    const responseData = error.response?.data;

    let code: ErrorCode | string = ErrorCode.INTERNAL_SERVER_ERROR;
    let message = error.message || 'An unexpected API error occurred.';
    let details: unknown = null;

    if (responseData) {
      // Check for standardized ApiErrorResponse envelope
      if ('error' in responseData && responseData.error) {
        code = responseData.error.code || ErrorCode.INTERNAL_SERVER_ERROR;
        message = responseData.error.message || message;
        details = responseData.error.details ?? null;
      } else if ('detail' in responseData && typeof responseData.detail === 'string') {
        // Fallback for standard FastAPI detail string
        message = responseData.detail;
        if (status === 404) code = ErrorCode.NOT_FOUND;
        else if (status === 403) code = ErrorCode.AUTH_FORBIDDEN;
        else if (status === 401) code = ErrorCode.AUTH_UNAUTHORIZED;
        else if (status === 422) code = ErrorCode.VALIDATION_ERROR;
      }
    } else if (error.code === 'ECONNABORTED') {
      code = ErrorCode.SERVICE_UNAVAILABLE;
      message = 'Request timeout connecting to backend engine.';
    } else if (!error.response) {
      code = ErrorCode.SERVICE_UNAVAILABLE;
      message = 'Network error: Unable to reach KEEP backend service.';
    }

    return Promise.reject(new ApiError(message, code, status, details));
  }
);

/**
 * Safely unwraps an ApiResponse[T] payload.
 */
export function unwrapData<T>(response: AxiosResponse<ApiResponse<T>>): T {
  return response.data.data;
}

/**
 * Normalizes any caught error into a typed ApiError instance.
 */
export function normalizeApiError(err: unknown): ApiError {
  if (err instanceof ApiError) {
    return err;
  }
  if (err instanceof Error) {
    return new ApiError(err.message, ErrorCode.INTERNAL_SERVER_ERROR);
  }
  return new ApiError('An unknown error occurred.', ErrorCode.INTERNAL_SERVER_ERROR);
}

export default apiClient;
