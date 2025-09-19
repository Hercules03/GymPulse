import React from 'react';
import { motion } from 'framer-motion';
import { User, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

interface ChatBubbleProps {
  message: Message;
}

export default function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.type === 'user';
  const isSystem = message.type === 'system';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div className={`flex items-end gap-2 max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
          isUser 
            ? 'bg-blue-500' 
            : isSystem 
              ? 'bg-green-500'
              : 'bg-gray-100'
        }`}>
          {isUser ? (
            <User className="w-4 h-4 text-white" />
          ) : isSystem ? (
            <div className="w-2 h-2 bg-white rounded-full" />
          ) : (
            <Bot className="w-4 h-4 text-gray-600" />
          )}
        </div>

        {/* Message Bubble */}
        <div className={`relative px-4 py-2 rounded-2xl shadow-sm ${
          isUser 
            ? 'bg-blue-500 text-white rounded-br-md' 
            : isSystem
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-gray-100 text-gray-800 rounded-bl-md'
        }`}>
          <div className="text-sm leading-relaxed">
            <ReactMarkdown
              components={{
                // Style markdown elements to match the chat bubble design
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
                ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-2">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-2">{children}</ol>,
                li: ({ children }) => <li className="ml-2">{children}</li>,
                h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
                code: ({ children, className }) => {
                  const isInline = !className;
                  return isInline ? (
                    <code className="bg-black bg-opacity-10 px-1 py-0.5 rounded text-xs font-mono">
                      {children}
                    </code>
                  ) : (
                    <pre className="bg-black bg-opacity-10 p-2 rounded text-xs font-mono overflow-x-auto mb-2">
                      <code>{children}</code>
                    </pre>
                  );
                },
                blockquote: ({ children }) => (
                  <blockquote className="border-l-2 border-gray-400 pl-3 italic mb-2">
                    {children}
                  </blockquote>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
          
          {/* Timestamp */}
          <div className={`text-xs mt-1 ${
            isUser 
              ? 'text-blue-100' 
              : isSystem
                ? 'text-green-600'
                : 'text-gray-500'
          }`}>
            {message.timestamp.toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </div>

          {/* Tail */}
          <div className={`absolute bottom-0 w-3 h-3 ${
            isUser 
              ? 'right-0 bg-blue-500 rounded-bl-full' 
              : isSystem
                ? 'left-0 bg-green-50 border-l border-b border-green-200'
                : 'left-0 bg-gray-100 rounded-br-full'
          }`} style={{
            transform: isUser ? 'translateX(8px)' : 'translateX(-8px)'
          }} />
        </div>
      </div>
    </motion.div>
  );
}