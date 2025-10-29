import { vi } from 'vitest';

// Create mocks that can be reconfigured
export const mockPostMessage = vi.fn().mockResolvedValue({ ok: true, ts: '1234567890.123456' });
export const mockConversationsList = vi.fn().mockResolvedValue({ channels: [] });

export class WebClient {
  public token: string;
  public chat: {
    postMessage: typeof mockPostMessage;
  };
  public conversations: {
    list: typeof mockConversationsList;
  };

  constructor(token: string) {
    this.token = token;
    this.chat = {
      postMessage: mockPostMessage,
    };
    this.conversations = {
      list: mockConversationsList,
    };
  }
}
