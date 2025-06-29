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
          // Load messages for this session if they haven't been loaded
          get().loadSessionMessages(sessionId);
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

        deleteSession: async (sessionId: string) => {
          try {
            // Delete from backend first
            await apiService.deleteSession(sessionId);
            console.log(`Deleted session ${sessionId} from backend`);
            
            // Then update local state
            set(state => ({
              sessions: state.sessions.filter(s => s.id !== sessionId),
              currentSessionId: state.currentSessionId === sessionId ? null : state.currentSessionId,
            }));
          } catch (error) {
            console.error('Failed to delete session from backend:', error);
            // Still remove from local state even if backend fails
            set(state => ({
              sessions: state.sessions.filter(s => s.id !== sessionId),
              currentSessionId: state.currentSessionId === sessionId ? null : state.currentSessionId,
            }));
          }
        },

        updateSessionTitle: async (sessionId: string, title: string) => {
          try {
            // Update backend first
            console.log(`Updating session ${sessionId} title to "${title}" in backend...`);
            await apiService.updateSessionTitle(sessionId, title);
            console.log(`✅ Successfully updated session ${sessionId} title to "${title}" in backend`);
            
            // Then update local state
            set(state => ({
              sessions: state.sessions.map(session => 
                session.id === sessionId 
                  ? { ...session, title, updatedAt: new Date() }
                  : session
              )
            }));
            console.log(`✅ Updated local state for session ${sessionId}`);
          } catch (error) {
            console.error('❌ Failed to update session title in backend:', error);
            // Still update local state for immediate UI feedback
            set(state => ({
              sessions: state.sessions.map(session => 
                session.id === sessionId 
                  ? { ...session, title, updatedAt: new Date() }
                  : session
              )
            }));
            console.log(`⚠️ Updated local state only for session ${sessionId}`);
          }
        },

        setIsTyping: (isTyping: boolean) => {
          set({ isTyping });
        },

        setTheme: (theme: 'light' | 'dark') => {
          set({ theme });
          document.documentElement.classList.toggle('dark', theme === 'dark');
        },

        sendMessage: async (content: string) => {
          let { currentSessionId, addMessage, updateSessionTitle } = get();
          
          if (!currentSessionId) {
            get().createSession();
            currentSessionId = get().currentSessionId;
          }

          // Check if this is the first message (before adding the message)
          const currentSession = get().sessions.find(s => s.id === currentSessionId);
          const isFirstMessage = !currentSession || currentSession.messages.length === 0;
          const isDefaultTitle = currentSession && currentSession.title.match(/^Chat \d{1,2}\/\d{1,2}\/\d{4}/);

          // Add user message immediately
          addMessage({ content, role: 'user' });

          try {
            console.log('Sending message via API:', content);
            console.log('Session ID:', currentSessionId);
            set({ isTyping: true });
            const response = await apiService.sendMessage(content, currentSessionId || undefined);
            console.log('API Response:', response);
            
            // Update session ID if backend returned a different one (for new sessions)
            if (response.session_id && response.session_id !== currentSessionId) {
              console.log('Updating session ID from backend:', response.session_id);
              const oldSessionId = currentSessionId;
              currentSessionId = response.session_id;
              set(state => ({
                currentSessionId: response.session_id,
                sessions: state.sessions.map(session => 
                  session.id === oldSessionId 
                    ? { ...session, id: response.session_id }
                    : session
                )
              }));
            }
            
            addMessage({ content: response.message, role: 'assistant' });
            
            // Update session title to first user message if this was the first message with default title
            if (isFirstMessage && isDefaultTitle && currentSessionId) {
              const newTitle = content.length > 50 ? content.slice(0, 50) + '...' : content;
              console.log('Auto-updating session title to:', newTitle);
              await updateSessionTitle(currentSessionId, newTitle);
            }
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

        loadSessionsFromBackend: async () => {
          try {
            console.log('Loading sessions from backend...');
            const backendSessions = await apiService.fetchSessions();
            console.log('Backend sessions:', backendSessions);
            
            // Debug: Log each session title
            backendSessions.forEach(session => {
              console.log(`Session ${session.id}: title="${session.title}"`);
            });
            
            if (backendSessions && backendSessions.length > 0) {
              // Convert backend sessions to frontend format
              const convertedSessions: ChatSession[] = backendSessions.map(session => ({
                id: session.id,
                title: session.title,
                messages: [], // Messages will be loaded separately when needed
                createdAt: new Date(session.created_at),
                updatedAt: new Date(session.updated_at),
              }));
              
              // Merge with existing sessions (avoid duplicates)
              const { sessions: currentSessions } = get();
              const existingIds = new Set(currentSessions.map(s => s.id));
              const newSessions = convertedSessions.filter(s => !existingIds.has(s.id));
              
              if (newSessions.length > 0) {
                console.log(`Adding ${newSessions.length} new sessions from backend`);
                set(state => ({
                  sessions: [...state.sessions, ...newSessions]
                }));
              }
            }
          } catch (error) {
            console.error('Failed to load sessions from backend:', error);
            // Don't throw error - app should still work with local sessions
          }
        },

        loadSessionMessages: async (sessionId: string) => {
          const { sessions } = get();
          const session = sessions.find(s => s.id === sessionId);
          
          // Only load if session exists and has no messages loaded
          if (session && session.messages.length === 0) {
            try {
              console.log(`Loading messages for session ${sessionId}...`);
              const historyResponse = await apiService.getChatHistory(sessionId);
              console.log('Session history:', historyResponse);
              
              if (historyResponse.messages && historyResponse.messages.length > 0) {
                // Convert backend messages to frontend format
                const convertedMessages: Message[] = historyResponse.messages.map(msg => ({
                  id: msg.id,
                  content: msg.content,
                  role: msg.role as 'user' | 'assistant',
                  timestamp: new Date(msg.timestamp),
                }));
                
                // Update session with messages
                set(state => ({
                  sessions: state.sessions.map(s => 
                    s.id === sessionId 
                      ? { ...s, messages: convertedMessages }
                      : s
                  )
                }));
                
                console.log(`Loaded ${convertedMessages.length} messages for session ${sessionId}`);
              }
            } catch (error) {
              console.error(`Failed to load messages for session ${sessionId}:`, error);
              // Don't throw error - session should still be usable
            }
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