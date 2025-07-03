import { useEffect, useState } from 'react';
import Sidebar from './components/sidebar/sidebar';
import ChatWindow from './components/chat/chat-window';
import { AuthComponent } from './components/auth/auth-component';
import { useChatStore } from './stores/chat-store';
import './styles/globals.css';

interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
}

function App() {
  const { theme, createSession, sessions, loadSessionsFromBackend } = useChatStore();
  const [authenticated, setAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  useEffect(() => {
    console.log('App mounted');
    console.log('Theme:', theme);
    console.log('Sessions:', sessions);
    
    // Set initial theme
    document.documentElement.classList.toggle('dark', theme === 'dark');
    
    // Handle OAuth callback with token
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    if (token) {
      // Store token and clean URL without reload
      localStorage.setItem('access_token', token);
      window.history.replaceState({}, document.title, window.location.pathname);
      // Let the auth component handle the status check naturally
      window.location.reload();
    }
  }, [theme]);

  // Load sessions from backend when authenticated
  useEffect(() => {
    if (authenticated) {
      const initializeApp = async () => {
        console.log('Initializing app for authenticated user...');
        
        // Load sessions from backend
        await loadSessionsFromBackend();
        
        // Then check if we need to create an initial session
        const { sessions: updatedSessions } = useChatStore.getState();
        if (updatedSessions.length === 0) {
          console.log('No sessions found, creating initial session...');
          createSession();
        } else {
          console.log(`Found ${updatedSessions.length} sessions from backend`);
        }
      };
      
      initializeApp();
    }
  }, [authenticated]);

  const handleAuthChange = (isAuthenticated: boolean, user?: User) => {
    setAuthenticated(isAuthenticated);
    setCurrentUser(user || null);
    
    if (!isAuthenticated) {
      // Clear sessions when user logs out
      useChatStore.setState({ sessions: [], currentSessionId: null });
    }
  };

  // Add error boundary
  try {
    return (
      <div className="flex h-screen bg-background">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex h-14 items-center justify-between px-6">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                  <span className="text-primary-foreground font-bold text-sm">AI</span>
                </div>
                <div>
                  <h1 className="text-lg font-semibold">Time Management AI Assistant</h1>
                  <p className="text-sm text-muted-foreground">
                    {currentUser ? `Welcome, ${currentUser.name}` : 'AI-powered analytics for your time management data'}
                  </p>
                </div>
              </div>
              <AuthComponent onAuthChange={handleAuthChange} />
            </div>
          </header>
          
          <main className="flex-1 overflow-hidden">
            {authenticated ? (
              <ChatWindow />
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <h2 className="text-xl font-semibold mb-2">Authentication Required</h2>
                  <p className="text-muted-foreground mb-4">Please login to access the AI assistant</p>
                  <div className="text-sm text-muted-foreground">
                    Click "Sign in with Google" in the top right corner to continue
                  </div>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    );
  } catch (error) {
    console.error('App render error:', error);
    return (
      <div className="min-h-screen bg-red-50 p-8">
        <h1 className="text-2xl font-bold text-red-600 mb-4">Error Loading App</h1>
        <pre className="bg-red-100 p-4 rounded text-sm">
          {error instanceof Error ? error.message : 'Unknown error'}
        </pre>
      </div>
    );
  }
}

export default App;