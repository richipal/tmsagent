export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  isLoading?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatStore {
  sessions: ChatSession[];
  currentSessionId: string | null;
  isConnected: boolean;
  isTyping: boolean;
  theme: 'light' | 'dark';
  
  // Actions
  createSession: () => void;
  setCurrentSession: (sessionId: string) => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateMessage: (messageId: string, updates: Partial<Message>) => void;
  deleteSession: (sessionId: string) => Promise<void>;
  updateSessionTitle: (sessionId: string, title: string) => Promise<void>;
  setIsTyping: (isTyping: boolean) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  sendMessage: (content: string) => Promise<void>;
  loadSessionsFromBackend: () => Promise<void>;
  loadSessionMessages: (sessionId: string) => Promise<void>;
}

export interface FileUpload {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  status: 'uploading' | 'completed' | 'error';
}