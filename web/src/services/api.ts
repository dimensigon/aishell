import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  ApiResponse,
  AuthTokens,
  LoginRequest,
  RegisterRequest,
  User,
  DatabaseConnection,
  QueryRequest,
  QueryResult,
  PerformanceMetric,
  AuditLog,
  PaginatedResponse,
} from '@types/index';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth tokens
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('accessToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refreshToken');
            const { data } = await axios.post('/api/auth/refresh', {
              refreshToken,
            });

            localStorage.setItem('accessToken', data.accessToken);
            this.client.defaults.headers.common['Authorization'] =
              `Bearer ${data.accessToken}`;

            return this.client(originalRequest);
          } catch (refreshError) {
            localStorage.clear();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<ApiResponse<AuthTokens & { user: User }>> {
    const { data } = await this.client.post('/auth/login', credentials);
    return data;
  }

  async register(userData: RegisterRequest): Promise<ApiResponse<User>> {
    const { data } = await this.client.post('/auth/register', userData);
    return data;
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout');
    localStorage.clear();
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    const { data } = await this.client.get('/auth/me');
    return data;
  }

  async enable2FA(): Promise<ApiResponse<{ qrCode: string; secret: string }>> {
    const { data } = await this.client.post('/auth/2fa/enable');
    return data;
  }

  async verify2FA(code: string): Promise<ApiResponse<boolean>> {
    const { data } = await this.client.post('/auth/2fa/verify', { code });
    return data;
  }

  // Database Connections
  async getConnections(): Promise<ApiResponse<DatabaseConnection[]>> {
    const { data } = await this.client.get('/connections');
    return data;
  }

  async getConnection(id: string): Promise<ApiResponse<DatabaseConnection>> {
    const { data } = await this.client.get(`/connections/${id}`);
    return data;
  }

  async createConnection(
    connection: Omit<DatabaseConnection, 'id' | 'status' | 'createdAt'>
  ): Promise<ApiResponse<DatabaseConnection>> {
    const { data } = await this.client.post('/connections', connection);
    return data;
  }

  async updateConnection(
    id: string,
    connection: Partial<DatabaseConnection>
  ): Promise<ApiResponse<DatabaseConnection>> {
    const { data } = await this.client.put(`/connections/${id}`, connection);
    return data;
  }

  async deleteConnection(id: string): Promise<ApiResponse<void>> {
    const { data } = await this.client.delete(`/connections/${id}`);
    return data;
  }

  async testConnection(id: string): Promise<ApiResponse<{ status: string }>> {
    const { data } = await this.client.post(`/connections/${id}/test`);
    return data;
  }

  // Query Execution
  async executeQuery(query: QueryRequest): Promise<ApiResponse<QueryResult>> {
    const { data } = await this.client.post('/queries/execute', query);
    return data;
  }

  async getQueryHistory(
    connectionId?: string,
    page = 1,
    pageSize = 20
  ): Promise<ApiResponse<PaginatedResponse<QueryResult>>> {
    const { data } = await this.client.get('/queries/history', {
      params: { connectionId, page, pageSize },
    });
    return data;
  }

  async getTableSchema(
    connectionId: string,
    tableName: string
  ): Promise<ApiResponse<any>> {
    const { data } = await this.client.get(
      `/connections/${connectionId}/schema/${tableName}`
    );
    return data;
  }

  async getTables(connectionId: string): Promise<ApiResponse<string[]>> {
    const { data } = await this.client.get(`/connections/${connectionId}/tables`);
    return data;
  }

  // Performance Metrics
  async getMetrics(
    connectionId: string,
    metric?: string,
    startTime?: string,
    endTime?: string
  ): Promise<ApiResponse<PerformanceMetric[]>> {
    const { data } = await this.client.get('/metrics', {
      params: { connectionId, metric, startTime, endTime },
    });
    return data;
  }

  // User Management
  async getUsers(
    page = 1,
    pageSize = 20
  ): Promise<ApiResponse<PaginatedResponse<User>>> {
    const { data } = await this.client.get('/users', {
      params: { page, pageSize },
    });
    return data;
  }

  async updateUser(id: string, userData: Partial<User>): Promise<ApiResponse<User>> {
    const { data } = await this.client.put(`/users/${id}`, userData);
    return data;
  }

  async deleteUser(id: string): Promise<ApiResponse<void>> {
    const { data } = await this.client.delete(`/users/${id}`);
    return data;
  }

  // Audit Logs
  async getAuditLogs(
    userId?: string,
    action?: string,
    page = 1,
    pageSize = 20
  ): Promise<ApiResponse<PaginatedResponse<AuditLog>>> {
    const { data } = await this.client.get('/audit', {
      params: { userId, action, page, pageSize },
    });
    return data;
  }

  // Export
  async exportData(
    format: 'csv' | 'json' | 'xlsx',
    queryResult: QueryResult
  ): Promise<Blob> {
    const { data } = await this.client.post(
      '/export',
      { format, queryResult },
      { responseType: 'blob' }
    );
    return data;
  }
}

export const api = new ApiService();
export default api;
