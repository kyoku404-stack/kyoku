import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import {
  apiClient,
  ApiError,
  unwrapData,
  normalizeApiError,
} from '@/services/api';
import {
  ErrorCode,
  isApiErrorResponse,
  isApiResponse,
  type ApiResponse,
} from '@/types/api';

interface InterceptorHandler<T> {
  fulfilled: (value: T) => T | Promise<T>;
  rejected: (error: unknown) => unknown;
}

interface InterceptorManagerMock<T> {
  handlers: Array<InterceptorHandler<T>>;
}

describe('API Client & Standardized Envelope Interceptors', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Type Guards', () => {
    it('correctly identifies valid ApiResponse', () => {
      const valid: ApiResponse<{ id: string }> = {
        success: true,
        message: 'Success',
        data: { id: '123' },
      };
      expect(isApiResponse(valid)).toBe(true);
      expect(isApiResponse({ success: false })).toBe(false);
      expect(isApiResponse(null)).toBe(false);
    });

    it('correctly identifies valid ApiErrorResponse', () => {
      const validError = {
        success: false,
        error: {
          code: ErrorCode.AUTH_INVALID_CREDENTIALS,
          message: 'Invalid email or password.',
          details: null,
        },
      };
      expect(isApiErrorResponse(validError)).toBe(true);
      expect(isApiErrorResponse({ success: true, data: {} })).toBe(false);
    });
  });

  describe('ApiError Class & Helper', () => {
    it('constructs ApiError with all fields', () => {
      const err = new ApiError(
        'Resource not found',
        ErrorCode.NOT_FOUND,
        404,
        { resource: 'Document' }
      );
      expect(err).toBeInstanceOf(Error);
      expect(err).toBeInstanceOf(ApiError);
      expect(err.name).toBe('ApiError');
      expect(err.message).toBe('Resource not found');
      expect(err.code).toBe(ErrorCode.NOT_FOUND);
      expect(err.status).toBe(404);
      expect(err.details).toEqual({ resource: 'Document' });
    });

    it('normalizes unknown error into ApiError', () => {
      const generic = new Error('Generic failure');
      const normalized = normalizeApiError(generic);
      expect(normalized).toBeInstanceOf(ApiError);
      expect(normalized.message).toBe('Generic failure');

      const nonError = normalizeApiError('Something bad');
      expect(nonError.message).toBe('An unknown error occurred.');
    });

    it('unwraps ApiResponse data correctly', () => {
      const mockResponse: AxiosResponse<ApiResponse<{ token: string }>> = {
        data: {
          success: true,
          message: 'Retrieved',
          data: { token: 'xyz' },
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as InternalAxiosRequestConfig,
      };
      expect(unwrapData(mockResponse)).toEqual({ token: 'xyz' });
    });
  });

  describe('Request Interceptor', () => {
    it('injects Bearer token and X-Request-ID into headers', async () => {
      localStorage.setItem('keep_auth_token', 'test_jwt_bearer_token');

      const requestManager = apiClient.interceptors.request as unknown as InterceptorManagerMock<InternalAxiosRequestConfig>;
      const requestInterceptor = requestManager.handlers[0];
      const config = { headers: {} } as InternalAxiosRequestConfig;

      const modified = (await requestInterceptor.fulfilled(config)) as InternalAxiosRequestConfig;
      expect(modified.headers?.Authorization).toBe('Bearer test_jwt_bearer_token');
      expect(modified.headers?.['X-Request-ID']).toMatch(/^req_\d+_/);
    });
  });

  describe('Response Error Interceptor', () => {
    it('unpacks backend standardized ApiErrorResponse envelope into ApiError', async () => {
      const responseManager = apiClient.interceptors.response as unknown as InterceptorManagerMock<unknown>;
      const responseInterceptor = responseManager.handlers[0];

      const mockAxiosError = {
        name: 'AxiosError',
        message: 'Request failed with status code 400',
        response: {
          status: 400,
          data: {
            success: false,
            error: {
              code: ErrorCode.VALIDATION_ERROR,
              message: 'Invalid input fields provided.',
              details: [{ loc: ['body', 'email'], msg: 'field required' }],
            },
          },
        },
      };

      await expect(responseInterceptor.rejected(mockAxiosError)).rejects.toMatchObject({
        name: 'ApiError',
        message: 'Invalid input fields provided.',
        code: ErrorCode.VALIDATION_ERROR,
        status: 400,
        details: [{ loc: ['body', 'email'], msg: 'field required' }],
      });
    });

    it('clears token on 401 Unauthorized status', async () => {
      localStorage.setItem('keep_auth_token', 'expired_token');
      const responseManager = apiClient.interceptors.response as unknown as InterceptorManagerMock<unknown>;
      const responseInterceptor = responseManager.handlers[0];

      const mock401Error = {
        name: 'AxiosError',
        message: 'Unauthorized',
        response: {
          status: 401,
          data: {
            success: false,
            error: {
              code: ErrorCode.AUTH_UNAUTHORIZED,
              message: 'Token has expired.',
            },
          },
        },
      };

      await expect(responseInterceptor.rejected(mock401Error)).rejects.toBeInstanceOf(ApiError);
      expect(localStorage.getItem('keep_auth_token')).toBeNull();
    });

    it('handles network error when response is undefined', async () => {
      const responseManager = apiClient.interceptors.response as unknown as InterceptorManagerMock<unknown>;
      const responseInterceptor = responseManager.handlers[0];

      const networkError = {
        name: 'AxiosError',
        message: 'Network Error',
        response: undefined,
      };

      await expect(responseInterceptor.rejected(networkError)).rejects.toMatchObject({
        name: 'ApiError',
        code: ErrorCode.SERVICE_UNAVAILABLE,
        message: 'Network error: Unable to reach KEEP backend service.',
      });
    });
  });
});
