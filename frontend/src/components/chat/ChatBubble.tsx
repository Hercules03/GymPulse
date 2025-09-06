import React from 'react';
import { motion } from 'framer-motion';
import { User, Bot } from 'lucide-react';

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
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
          
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