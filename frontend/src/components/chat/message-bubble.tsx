import React from 'react';
import { Message } from '@/types/chat';
import { cn } from '@/lib/utils';
import { User, Bot, Loader2 } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useChatStore } from '@/stores/chat-store';

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const { theme } = useChatStore();
  
  const isUser = message.role === 'user';
  const isLoading = message.isLoading;

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const renderContent = (content: string) => {
    // Handle both code blocks and images
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
    
    const parts = [];
    let processedContent = content;
    let partIndex = 0;

    // First, replace images with placeholders and collect image data
    const images: { placeholder: string; alt: string; src: string }[] = [];
    processedContent = processedContent.replace(imageRegex, (match, alt, src) => {
      const placeholder = `__IMAGE_PLACEHOLDER_${images.length}__`;
      // Convert relative URLs to absolute
      const absoluteSrc = src.startsWith('/') ? `http://localhost:8000${src}` : src;
      images.push({ placeholder, alt, src: absoluteSrc });
      return placeholder;
    });

    // Then process code blocks
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(processedContent)) !== null) {
      // Add text before code block (may contain image placeholders)
      if (match.index > lastIndex) {
        const textPart = processedContent.slice(lastIndex, match.index);
        parts.push(
          <div key={`text-${partIndex++}`} className="whitespace-pre-wrap">
            {renderTextWithImages(textPart, images)}
          </div>
        );
      }

      // Add code block
      const language = match[1] || 'text';
      const code = match[2];
      parts.push(
        <SyntaxHighlighter
          key={`code-${partIndex++}`}
          language={language}
          style={theme === 'dark' ? oneDark : oneLight}
          className="rounded-md text-sm"
        >
          {code}
        </SyntaxHighlighter>
      );

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text (may contain image placeholders)
    if (lastIndex < processedContent.length) {
      const textPart = processedContent.slice(lastIndex);
      parts.push(
        <div key={`text-${partIndex++}`} className="whitespace-pre-wrap">
          {renderTextWithImages(textPart, images)}
        </div>
      );
    }

    return parts.length > 0 ? parts : (
      <div className="whitespace-pre-wrap">
        {renderTextWithImages(processedContent, images)}
      </div>
    );
  };

  const renderTextWithImages = (text: string, images: { placeholder: string; alt: string; src: string }[]) => {
    if (images.length === 0) {
      return text;
    }

    const parts = [];
    let remainingText = text;

    images.forEach((image, index) => {
      const placeholderIndex = remainingText.indexOf(image.placeholder);
      if (placeholderIndex !== -1) {
        // Add text before placeholder
        if (placeholderIndex > 0) {
          parts.push(remainingText.slice(0, placeholderIndex));
        }
        
        // Add image
        parts.push(
          <img
            key={`img-${index}`}
            src={image.src}
            alt={image.alt}
            className="max-w-full h-auto rounded-lg shadow-md my-2 border"
            onError={(e) => {
              console.error('Failed to load image:', image.src);
              e.currentTarget.style.display = 'none';
            }}
          />
        );
        
        // Update remaining text
        remainingText = remainingText.slice(placeholderIndex + image.placeholder.length);
      }
    });

    // Add any remaining text
    if (remainingText) {
      parts.push(remainingText);
    }

    return parts;
  };

  return (
    <div
      className={cn(
        'flex w-full gap-3 px-4 py-3',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted text-muted-foreground'
        )}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      <div
        className={cn(
          'flex flex-col gap-1 max-w-[70%]',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        <div
          className={cn(
            'rounded-lg px-4 py-2 text-sm',
            isUser
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground'
          )}
        >
          {isLoading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Thinking...</span>
            </div>
          ) : (
            renderContent(message.content)
          )}
        </div>
        
        <span className="text-xs text-muted-foreground">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
};

export default MessageBubble;