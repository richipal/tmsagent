const API_BASE_URL = 'http://localhost:8000/api';

export class ApiService {
  private static instance: ApiService;

  private constructor() {}

  static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService();
    }
    return ApiService.instance;
  }

  async sendMessage(message: string, sessionId?: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/chat/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getChatHistory(sessionId: string): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/chat/history/${sessionId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async uploadFile(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async exportChat(sessionId: string, format: 'json' | 'csv' | 'txt'): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/chat/export/${sessionId}?format=${format}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.blob();
  }
}