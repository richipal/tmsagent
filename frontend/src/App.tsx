import { useEffect } from 'react';
import Sidebar from './components/sidebar/sidebar';
import ChatWindow from './components/chat/chat-window';
import { useChatStore } from './stores/chat-store';
import './styles/globals.css';

function App() {
  const { theme, createSession, sessions } = useChatStore();

  useEffect(() => {
    console.log('App mounted');
    console.log('Theme:', theme);
    console.log('Sessions:', sessions);
    
    // Set initial theme
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  useEffect(() => {
    console.log('Sessions length:', sessions.length);
    // Create initial session if none exists
    if (sessions.length === 0) {
      console.log('Creating initial session...');
      createSession();
    }
  }, [sessions.length, createSession]);

  // Add error boundary
  try {
    return (
      <div className="flex h-screen bg-background">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex h-14 items-center px-6">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                  <span className="text-primary-foreground font-bold text-sm">AI</span>
                </div>
                <div>
                  <h1 className="text-lg font-semibold">ADK Data Science Assistant</h1>
                  <p className="text-sm text-muted-foreground">Powered by Google ADK</p>
                </div>
              </div>
            </div>
          </header>
          
          <main className="flex-1 overflow-hidden">
            <ChatWindow />
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