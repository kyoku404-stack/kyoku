export interface ApiErrorResponse {
  error: string;
  message: string;
  detail?: string | null;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  timestamp?: string;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}
