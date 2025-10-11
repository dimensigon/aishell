import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import api from '@services/api';

vi.mock('axios');

describe('ApiService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('sends login request with credentials', async () => {
      const mockResponse = {
        data: {
          success: true,
          data: {
            accessToken: 'token123',
            refreshToken: 'refresh123',
            expiresIn: 1800,
            user: {
              id: '1',
              username: 'testuser',
              email: 'test@example.com',
              role: 'user',
              twoFactorEnabled: false,
              createdAt: '2024-01-01',
            },
          },
        },
      };

      (axios.create as any).mockReturnValue({
        post: vi.fn().mockResolvedValue(mockResponse),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      });

      const result = await api.login({
        username: 'testuser',
        password: 'password123',
      });

      expect(result.success).toBe(true);
      expect(result.data?.accessToken).toBe('token123');
    });
  });

  describe('getConnections', () => {
    it('fetches database connections', async () => {
      const mockConnections = [
        {
          id: '1',
          name: 'Test DB',
          type: 'postgresql',
          host: 'localhost',
          port: 5432,
          database: 'testdb',
          username: 'testuser',
          ssl: false,
          status: 'connected',
          createdAt: '2024-01-01',
        },
      ];

      const mockResponse = {
        data: {
          success: true,
          data: mockConnections,
        },
      };

      (axios.create as any).mockReturnValue({
        get: vi.fn().mockResolvedValue(mockResponse),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      });

      const result = await api.getConnections();

      expect(result.success).toBe(true);
      expect(result.data).toHaveLength(1);
      expect(result.data?.[0].name).toBe('Test DB');
    });
  });
});
