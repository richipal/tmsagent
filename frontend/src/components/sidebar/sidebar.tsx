import React from 'react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { useChatStore } from '@/stores/chat-store';
import { Plus, MessageSquare, Sun, Moon, Download, Search } from 'lucide-react';
import { cn } from '@/lib/utils';

const Sidebar: React.FC = () => {
  const {
    sessions,
    currentSessionId,
    createSession,
    setCurrentSession,
    deleteSession,
    theme,
    setTheme,
  } = useChatStore();

  const handleThemeToggle = (checked: boolean) => {
    setTheme(checked ? 'dark' : 'light');
  };

  const formatSessionTitle = (session: any) => {
    if (session.messages.length === 0) {
      return session.title;
    }
    const firstMessage = session.messages[0];
    return firstMessage.content.slice(0, 30) + (firstMessage.content.length > 30 ? '...' : '');
  };

  return (
    <div className="w-80 border-r bg-muted/10 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Chat Sessions</h2>
          <Button
            onClick={createSession}
            size="icon"
            variant="outline"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        
        {/* Theme Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sun className="h-4 w-4" />
            <span className="text-sm">Light</span>
          </div>
          <Switch
            checked={theme === 'dark'}
            onCheckedChange={handleThemeToggle}
          />
          <div className="flex items-center gap-2">
            <Moon className="h-4 w-4" />
            <span className="text-sm">Dark</span>
          </div>
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-auto p-2">
        {sessions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No chat sessions yet</p>
            <p className="text-xs">Create a new session to get started</p>
          </div>
        ) : (
          <div className="space-y-2">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={cn(
                  "group relative rounded-lg p-3 cursor-pointer transition-colors",
                  "hover:bg-accent hover:text-accent-foreground",
                  currentSessionId === session.id
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground"
                )}
                onClick={() => setCurrentSession(session.id)}
              >
                <div className="flex items-start gap-2">
                  <MessageSquare className="h-4 w-4 mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {formatSessionTitle(session)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Intl.DateTimeFormat('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      }).format(session.updatedAt)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {session.messages.length} messages
                    </p>
                  </div>
                </div>
                
                {/* Delete button - shows on hover */}
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute top-2 right-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(session.id);
                  }}
                >
                  ×
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t space-y-2">
        <Button variant="outline" className="w-full justify-start" size="sm">
          <Search className="h-4 w-4 mr-2" />
          Search Messages
        </Button>
        <Button variant="outline" className="w-full justify-start" size="sm">
          <Download className="h-4 w-4 mr-2" />
          Export Chat
        </Button>
      </div>
    </div>
  );
};

export default Sidebar;