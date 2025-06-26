import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { ChatStore, ChatSession, Message } from '../types/chat';
import { ApiService } from '../services/api';

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => {
      const apiService = ApiService.getInstance();

      return {
        sessions: [],
        currentSessionId: null,
        isConnected: false,
        isTyping: false,
        theme: 'light',

        createSession: () => {
          const newSession: ChatSession = {
            id: crypto.randomUUID(),
            title: `Chat ${new Date().toLocaleDateString()}`,
            messages: [],
            createdAt: new Date(),
            updatedAt: new Date(),
          };

          set(state => ({
            sessions: [...state.sessions, newSession],
            currentSessionId: newSession.id,
          }));
        },

        setCurrentSession: (sessionId: string) => {
          set({ currentSessionId: sessionId });
        },

        addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => {
          const { sessions, currentSessionId } = get();
          const newMessage: Message = {
            ...message,
            id: crypto.randomUUID(),
            timestamp: new Date(),
          };

          const updatedSessions = sessions.map(session =>
            session.id === currentSessionId
              ? {
                  ...session,
                  messages: [...session.messages, newMessage],
                  updatedAt: new Date(),
                }
              : session
          );

          set({ sessions: updatedSessions });
        },

        updateMessage: (messageId: string, updates: Partial<Message>) => {
          const { sessions, currentSessionId } = get();
          
          const updatedSessions = sessions.map(session =>
            session.id === currentSessionId
              ? {
                  ...session,
                  messages: session.messages.map(msg =>
                    msg.id === messageId ? { ...msg, ...updates } : msg
                  ),
                  updatedAt: new Date(),
                }
              : session
          );

          set({ sessions: updatedSessions });
        },

        deleteSession: (sessionId: string) => {
          set(state => ({
            sessions: state.sessions.filter(s => s.id !== sessionId),
            currentSessionId: state.currentSessionId === sessionId ? null : state.currentSessionId,
          }));
        },

        setIsTyping: (isTyping: boolean) => {
          set({ isTyping });
        },

        setTheme: (theme: 'light' | 'dark') => {
          set({ theme });
          document.documentElement.classList.toggle('dark', theme === 'dark');
        },

        sendMessage: async (content: string) => {
          const { currentSessionId, addMessage } = get();
          
          if (!currentSessionId) {
            get().createSession();
          }

          // Add user message immediately
          addMessage({ content, role: 'user' });

          try {
            console.log('Sending message via API:', content);
            console.log('Session ID:', currentSessionId);
            set({ isTyping: true });
            const response = await apiService.sendMessage(content, currentSessionId || undefined);
            console.log('API Response:', response);
            addMessage({ content: response.message, role: 'assistant' });
          } catch (error) {
            console.error('Failed to send message:', error);
            console.error('Error details:', {
              name: error instanceof Error ? error.name : 'Unknown',
              message: error instanceof Error ? error.message : String(error),
              stack: error instanceof Error ? error.stack : undefined
            });
            addMessage({ 
              content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : String(error)}. Please try again.`, 
              role: 'assistant' 
            });
          } finally {
            set({ isTyping: false });
          }
        },
      };
    },
    {
      name: 'chat-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        sessions: state.sessions,
        currentSessionId: state.currentSessionId,
        theme: state.theme,
      }),
    }
  )
);