const API_BASE_URL = 'http://localhost:8000/api';
const AUTH_BASE_URL = 'http://localhost:8000';

export class ApiService {
  private static instance: ApiService;
  private authToken: string | null = null;

  private constructor() {
    // Try to load token from localStorage
    this.authToken = localStorage.getItem('access_token');
  }

  static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService();
    }
    return ApiService.instance;
  }

  private getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    
    return headers;
  }

  setAuthToken(token: string) {
    this.authToken = token;
    localStorage.setItem('access_token', token);
  }

  clearAuthToken() {
    this.authToken = null;
    localStorage.removeItem('access_token');
  }

  async sendMessage(message: string, sessionId?: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/chat/send`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
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
    const response = await fetch(`${API_BASE_URL}/chat/history/${sessionId}`, {
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async fetchSessions(): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.sessions || [];
  }

  async deleteSession(sessionId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/chat/session/${sessionId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  }

  async updateSessionTitle(sessionId: string, title: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/chat/session/${sessionId}/title`, {
      method: 'PATCH',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ title }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  }

  // Authentication methods
  async getAuthStatus(): Promise<any> {
    const response = await fetch(`${AUTH_BASE_URL}/auth/status`, {
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async devLogin(userId: string = 'dev_user'): Promise<any> {
    const response = await fetch(`${AUTH_BASE_URL}/auth/dev-login?user_id=${userId}`, {
      method: 'GET',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    if (data.access_token) {
      this.setAuthToken(data.access_token);
    }
    
    return data;
  }

  async logout(): Promise<void> {
    await fetch(`${AUTH_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    
    this.clearAuthToken();
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