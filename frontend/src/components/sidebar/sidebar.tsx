import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { useChatStore } from '@/stores/chat-store';
import { Plus, MessageSquare, Sun, Moon, Download, Search, Edit2, Check, X, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

const Sidebar: React.FC = () => {
  const {
    sessions,
    currentSessionId,
    createSession,
    setCurrentSession,
    deleteSession,
    updateSessionTitle,
    loadSessionMessages,
    theme,
    setTheme,
  } = useChatStore();

  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleThemeToggle = (checked: boolean) => {
    setTheme(checked ? 'dark' : 'light');
  };

  const formatSessionTitle = (session: any) => {
    // Always show the actual saved title - no more auto-formatting
    // The title should be updated at the backend level when needed
    return session.title;
  };

  const startEditing = (session: any, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    // Use the actual session title, not the formatted one
    setEditingTitle(session.title);
    console.log('Starting edit for session:', session.id, 'with title:', session.title);
  };

  const cancelEditing = () => {
    setEditingSessionId(null);
    setEditingTitle('');
  };

  const saveTitle = async (sessionId: string) => {
    const newTitle = editingTitle.trim();
    if (newTitle && newTitle !== '') {
      try {
        await updateSessionTitle(sessionId, newTitle);
        console.log(`Updated session title to: ${newTitle}`);
      } catch (error) {
        console.error('Failed to update session title:', error);
        // Optionally show an error toast here
      }
    } else {
      // If empty title, restore original title
      const session = sessions.find(s => s.id === sessionId);
      if (session) {
        setEditingTitle(session.title);
        return; // Don't cancel editing, let user try again
      }
    }
    cancelEditing();
  };

  const handleKeyPress = (e: React.KeyboardEvent, sessionId: string) => {
    if (e.key === 'Enter') {
      saveTitle(sessionId);
    } else if (e.key === 'Escape') {
      cancelEditing();
    }
  };

  const handleContextMenu = (e: React.MouseEvent, session: any) => {
    e.preventDefault();
    if (editingSessionId !== session.id) {
      startEditing(session, e);
    }
  };

  const performSearch = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    const queryLower = query.toLowerCase().trim();

    try {
      // Search through all sessions and their messages
      const searchPromises = sessions.map(async (session) => {
        // Ensure messages are loaded for this session
        if (session.messages.length === 0) {
          await loadSessionMessages(session.id);
        }
        
        // Get fresh session data from store after loading messages
        const { sessions: updatedSessions } = useChatStore.getState();
        const updatedSession = updatedSessions.find(s => s.id === session.id) || session;
        
        // Search through messages in this session
        const sessionResults: any[] = [];
        updatedSession.messages.forEach((message, messageIndex) => {
          if (message.content.toLowerCase().includes(queryLower)) {
            sessionResults.push({
              sessionId: session.id,
              sessionTitle: session.title,
              message: message,
              messageIndex: messageIndex,
              context: {
                before: updatedSession.messages[messageIndex - 1] || null,
                after: updatedSession.messages[messageIndex + 1] || null,
              }
            });
          }
        });
        
        return sessionResults;
      });

      // Wait for all sessions to be searched
      const allResults = await Promise.all(searchPromises);
      const flatResults = allResults.flat();
      
      setSearchResults(flatResults);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [sessions, loadSessionMessages]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // Debounce search by 300ms
    searchTimeoutRef.current = setTimeout(() => {
      performSearch(query);
    }, 300);
  };

  const goToMessage = (sessionId: string) => {
    setCurrentSession(sessionId);
    setIsSearchOpen(false);
    setSearchQuery('');
    setSearchResults([]);
  };

  // Cleanup timeout on unmount and add keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsSearchOpen(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text;
    
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, index) => 
      part.toLowerCase() === query.toLowerCase() ? 
        <mark key={index} className="bg-yellow-200 dark:bg-yellow-600">{part}</mark> : part
    );
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
                  "group relative rounded-lg p-3 transition-colors",
                  editingSessionId === session.id 
                    ? "bg-muted border-2 border-primary cursor-default" 
                    : "cursor-pointer hover:bg-accent hover:text-accent-foreground",
                  currentSessionId === session.id && editingSessionId !== session.id
                    ? "bg-accent text-accent-foreground"
                    : editingSessionId !== session.id ? "text-muted-foreground" : ""
                )}
                onClick={() => {
                  if (editingSessionId !== session.id) {
                    setCurrentSession(session.id);
                  }
                }}
                onContextMenu={(e) => handleContextMenu(e, session)}
              >
                <div className="flex items-start gap-2">
                  <MessageSquare className="h-4 w-4 mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    {editingSessionId === session.id ? (
                      /* Editing mode */
                      <div className="flex items-center gap-1 mb-1">
                        <Input
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onKeyDown={(e) => handleKeyPress(e, session.id)}
                          className="h-6 text-sm font-medium"
                          autoFocus
                          onBlur={(e) => {
                            // Only save on blur if not clicking on save/cancel buttons
                            setTimeout(() => {
                              if (editingSessionId === session.id) {
                                saveTitle(session.id);
                              }
                            }, 100);
                          }}
                        />
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-5 w-5 shrink-0"
                          onClick={(e) => {
                            e.stopPropagation();
                            saveTitle(session.id);
                          }}
                          onMouseDown={(e) => e.preventDefault()} // Prevent input blur
                        >
                          <Check className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-5 w-5 shrink-0"
                          onClick={(e) => {
                            e.stopPropagation();
                            cancelEditing();
                          }}
                          onMouseDown={(e) => e.preventDefault()} // Prevent input blur
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    ) : (
                      /* Display mode */
                      <div className="flex items-center gap-1 group/title pr-6">
                        <p className="text-sm font-medium truncate flex-1">
                          {formatSessionTitle(session)}
                        </p>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                          onClick={(e) => startEditing(session, e)}
                          title="Rename session"
                        >
                          <Edit2 className="h-3 w-3" />
                        </Button>
                      </div>
                    )}
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
                {editingSessionId !== session.id && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-1 right-1 h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(session.id);
                    }}
                    title="Delete session"
                  >
                    ×
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t space-y-2">
        <Dialog open={isSearchOpen} onOpenChange={(open) => {
          setIsSearchOpen(open);
          if (!open) {
            // Clear search when dialog closes
            setSearchQuery('');
            setSearchResults([]);
            if (searchTimeoutRef.current) {
              clearTimeout(searchTimeoutRef.current);
            }
          }
        }}>
          <DialogTrigger asChild>
            <Button variant="outline" className="w-full justify-between" size="sm">
              <div className="flex items-center">
                <Search className="h-4 w-4 mr-2" />
                Search Messages
              </div>
              <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground ml-auto">
                <span className="text-xs">⌘</span>K
              </kbd>
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[80vh]">
            <DialogHeader>
              <DialogTitle>Search Messages</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <Input
                placeholder="Search through all your messages..."
                value={searchQuery}
                onChange={handleSearchChange}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') {
                    setIsSearchOpen(false);
                    setSearchQuery('');
                    setSearchResults([]);
                  }
                }}
                className="w-full"
                autoFocus
              />
              
              {searchQuery && (
                <div className="text-sm text-muted-foreground">
                  {isSearching 
                    ? 'Searching...'
                    : searchResults.length > 0 
                      ? `Found ${searchResults.length} result${searchResults.length === 1 ? '' : 's'}`
                      : 'No results found'
                  }
                </div>
              )}
              
              <ScrollArea className="h-[400px]">
                <div className="space-y-3">
                  {searchResults.map((result, index) => (
                    <div
                      key={`${result.sessionId}-${result.messageIndex}-${index}`}
                      className="border rounded-lg p-3 hover:bg-accent cursor-pointer transition-colors"
                      onClick={() => goToMessage(result.sessionId)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="text-xs">
                            {result.sessionTitle}
                          </Badge>
                          <Badge variant={result.message.role === 'user' ? 'default' : 'outline'} className="text-xs">
                            {result.message.role === 'user' ? 'You' : 'Assistant'}
                          </Badge>
                        </div>
                        <ArrowRight className="h-4 w-4 text-muted-foreground" />
                      </div>
                      
                      <div className="text-sm">
                        {highlightText(
                          result.message.content.length > 200 
                            ? result.message.content.substring(0, 200) + '...' 
                            : result.message.content,
                          searchQuery
                        )}
                      </div>
                      
                      {result.context.before && (
                        <div className="mt-2 text-xs text-muted-foreground border-l-2 border-muted pl-2">
                          <span className="font-medium">Previous: </span>
                          {result.context.before.content.substring(0, 100)}
                          {result.context.before.content.length > 100 ? '...' : ''}
                        </div>
                      )}
                    </div>
                  ))}
                  
                  {searchQuery && !isSearching && searchResults.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No messages found containing "{searchQuery}"</p>
                      <p className="text-xs mt-1">Try a different search term</p>
                    </div>
                  )}
                  
                  {!searchQuery && (
                    <div className="text-center py-8 text-muted-foreground">
                      <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Search through all your chat messages</p>
                      <p className="text-xs mt-1">Type a keyword to get started</p>
                    </div>
                  )}
                  
                  {isSearching && (
                    <div className="text-center py-8 text-muted-foreground">
                      <div className="animate-spin h-8 w-8 border-2 border-current border-t-transparent rounded-full mx-auto mb-4"></div>
                      <p>Searching through messages...</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          </DialogContent>
        </Dialog>
        
        <Button variant="outline" className="w-full justify-start" size="sm">
          <Download className="h-4 w-4 mr-2" />
          Export Chat
        </Button>
        <div className="pt-2 text-xs text-muted-foreground">
          <p>💡 Tip: Click the edit icon or right-click to rename sessions</p>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;