import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Paperclip, Loader2 } from 'lucide-react';
import { useChatStore } from '@/stores/chat-store';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  suggestedQuestion?: string;
}

const ChatInput: React.FC<ChatInputProps> = ({ suggestedQuestion }) => {
  const [message, setMessage] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const { sendMessage, isTyping, currentSessionId, createSession } = useChatStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!message.trim() || isTyping) return;

    // Create session if none exists
    if (!currentSessionId) {
      createSession();
    }

    const messageToSend = message.trim();
    setMessage('');
    
    try {
      await sendMessage(messageToSend);
      // Refocus the input after sending
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      }, 100);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Refocus even on error
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      }, 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      // Handle file upload logic here
      console.log('File uploaded:', file.name);
    } catch (error) {
      console.error('File upload failed:', error);
    } finally {
      setIsUploading(false);
    }
  };

  // Auto-focus textarea on mount
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  // Update message when suggested question changes
  useEffect(() => {
    if (suggestedQuestion) {
      setMessage(suggestedQuestion);
      // Focus textarea after setting the message
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
          // Move cursor to end of text
          textareaRef.current.setSelectionRange(
            suggestedQuestion.length,
            suggestedQuestion.length
          );
        }
      }, 50);
    }
  }, [suggestedQuestion]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  return (
    <div className="border-t bg-background p-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className={cn(
              "min-h-[44px] max-h-32 resize-none pr-12",
              "focus:ring-2 focus:ring-primary focus:border-transparent"
            )}
            rows={1}
            disabled={isTyping}
          />
          
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="absolute right-2 top-2 h-8 w-8"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading || isTyping}
          >
            {isUploading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Paperclip className="h-4 w-4" />
            )}
          </Button>
        </div>
        
        <Button
          type="submit"
          size="icon"
          disabled={!message.trim() || isTyping}
          className="h-11 w-11"
        >
          {isTyping ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </form>
      
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileUpload}
        className="hidden"
        accept=".csv,.json,.txt,.pdf,.xlsx"
      />
      
      {isTyping && (
        <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
          <div className="flex space-x-1">
            <div className="h-2 w-2 bg-current rounded-full animate-bounce" />
            <div className="h-2 w-2 bg-current rounded-full animate-bounce [animation-delay:0.1s]" />
            <div className="h-2 w-2 bg-current rounded-full animate-bounce [animation-delay:0.2s]" />
          </div>
          <span>AI is typing...</span>
        </div>
      )}
    </div>
  );
};

export default ChatInput;