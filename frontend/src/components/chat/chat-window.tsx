import React, { useEffect, useRef, useState } from 'react';
import { useChatStore } from '@/stores/chat-store';
import MessageBubble from './message-bubble';
import ChatInput from './chat-input';
import SuggestedQuestions from './suggested-questions';
// import { ScrollArea } from '@radix-ui/react-scroll-area';

const ChatWindow: React.FC = () => {
  const { sessions, currentSessionId } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [suggestedQuestion, setSuggestedQuestion] = useState<string>('');
  
  const currentSession = sessions.find(s => s.id === currentSessionId);
  const messages = currentSession?.messages || [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleQuestionClick = (question: string) => {
    setSuggestedQuestion(question);
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-auto">
          <div className="flex flex-col h-full">
            {messages.length === 0 ? (
              <>
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center space-y-4">
                    <div className="text-4xl">🤖</div>
                    <h3 className="text-lg font-semibold">Welcome to ADK Data Science Assistant</h3>
                    <p className="text-muted-foreground max-w-md">
                      I'm here to help you with data analysis, visualization, and insights.
                      Upload your data files or ask me questions to get started!
                    </p>
                  </div>
                </div>
                <SuggestedQuestions 
                  onQuestionClick={handleQuestionClick}
                  isVisible={true}
                />
              </>
            ) : (
              <>
                {messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}
                <div ref={messagesEndRef} />
                
                {/* Show suggested questions after the last assistant message */}
                {messages.length > 0 && messages[messages.length - 1]?.role === 'assistant' && (
                  <SuggestedQuestions 
                    onQuestionClick={handleQuestionClick}
                    isVisible={true}
                  />
                )}
              </>
            )}
          </div>
        </div>
      </div>
      
      <ChatInput suggestedQuestion={suggestedQuestion} />
    </div>
  );
};

export default ChatWindow;