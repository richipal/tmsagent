import React, { useEffect, useRef } from 'react';
import { useChatStore } from '@/stores/chat-store';
import MessageBubble from './message-bubble';
import ChatInput from './chat-input';
// import { ScrollArea } from '@radix-ui/react-scroll-area';

const ChatWindow: React.FC = () => {
  const { sessions, currentSessionId } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const currentSession = sessions.find(s => s.id === currentSessionId);
  const messages = currentSession?.messages || [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-auto">
          <div className="flex flex-col">
            {messages.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <div className="text-center space-y-4">
                  <div className="text-4xl">🤖</div>
                  <h3 className="text-lg font-semibold">Welcome to ADK Data Science Assistant</h3>
                  <p className="text-muted-foreground max-w-md">
                    I'm here to help you with data analysis, visualization, and insights.
                    Upload your data files or ask me questions to get started!
                  </p>
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>
        </div>
      </div>
      
      <ChatInput />
    </div>
  );
};

export default ChatWindow;