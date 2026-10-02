/**
 * KEEP Enterprise Platform — Core API Types & Standardized Envelope Definitions.
 * Aligned with backend schemas (backend/app/schemas/envelope.py) and constants (backend/app/core/constants.py).
 */

/**
 * Standardized Machine-Readable Error Codes matching backend ErrorCode enum.
 */
export enum ErrorCode {
  // Authentication & Authorization
  AUTH_INVALID_CREDENTIALS = 'AUTH_INVALID_CREDENTIALS',
  AUTH_TOKEN_EXPIRED = 'AUTH_TOKEN_EXPIRED',
  AUTH_TOKEN_INVALID = 'AUTH_TOKEN_INVALID',
  AUTH_UNAUTHORIZED = 'AUTH_UNAUTHORIZED',
  AUTH_FORBIDDEN = 'AUTH_FORBIDDEN',

  // Validation & Requests
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  INVALID_REQUEST = 'INVALID_REQUEST',
  UNSUPPORTED_FILE_TYPE = 'UNSUPPORTED_FILE_TYPE',
  FILE_SIZE_EXCEEDED = 'FILE_SIZE_EXCEEDED',

  // Resource & Data
  NOT_FOUND = 'NOT_FOUND',
  CONFLICT = 'CONFLICT',
  DATABASE_ERROR = 'DATABASE_ERROR',
  TENANT_MISMATCH = 'TENANT_MISMATCH',

  // AI & Pipeline
  AI_INFERENCE_ERROR = 'AI_INFERENCE_ERROR',
  SEARCH_QUERY_ERROR = 'SEARCH_QUERY_ERROR',

  // Server Errors
  INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
}

/**
 * Detailed error object enclosed in ApiErrorResponse.
 */
export interface ApiErrorDetail {
  code: ErrorCode | string;
  message: string;
  details?: unknown;
}

/**
 * Standardized API Error Response Envelope (success: false).
 */
export interface ApiErrorResponse {
  success: false;
  error: ApiErrorDetail;
}

/**
 * Standardized API Success Response Envelope (success: true).
 */
export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

/**
 * Standardized Paginated Collection Container matching PaginatedData[T].
 */
export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Standard pagination query parameters.
 */
export interface PaginationParams {
  page?: number;
  page_size?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}

/**
 * Backward compatibility alias for legacy paginated responses.
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

/**
 * Type guard for ApiErrorResponse.
 */
export function isApiErrorResponse(data: unknown): data is ApiErrorResponse {
  return (
    typeof data === 'object' &&
    data !== null &&
    'success' in data &&
    (data as ApiErrorResponse).success === false &&
    'error' in data &&
    typeof (data as ApiErrorResponse).error === 'object' &&
    (data as ApiErrorResponse).error !== null &&
    'code' in (data as ApiErrorResponse).error &&
    'message' in (data as ApiErrorResponse).error
  );
}

/**
 * Type guard for ApiResponse<T>.
 */
export function isApiResponse<T>(data: unknown): data is ApiResponse<T> {
  return (
    typeof data === 'object' &&
    data !== null &&
    'success' in data &&
    (data as ApiResponse<T>).success === true &&
    'data' in data
  );
}
