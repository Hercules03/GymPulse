import React from 'react';
import { motion } from 'framer-motion';
import { MessageCircle, X } from 'lucide-react';

interface FloatingChatButtonProps {
  isOpen: boolean;
  onClick: () => void;
  hasUnreadMessages?: boolean;
}

export default function FloatingChatButton({ isOpen, onClick, hasUnreadMessages = false }: FloatingChatButtonProps) {
  return (
    <motion.button
      onClick={onClick}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className={`fixed bottom-4 right-4 z-40 w-14 h-14 rounded-full shadow-lg transition-all duration-300 flex items-center justify-center ${
        isOpen 
          ? 'bg-gray-100 text-gray-600 hover:bg-gray-200' 
          : 'bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700'
      }`}
    >
      {/* Notification Badge */}
      {hasUnreadMessages && !isOpen && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center"
        >
          <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
        </motion.div>
      )}

      {/* Icon */}
      <motion.div
        animate={{ rotate: isOpen ? 180 : 0 }}
        transition={{ duration: 0.2 }}
      >
        {isOpen ? (
          <X className="w-6 h-6" />
        ) : (
          <MessageCircle className="w-6 h-6" />
        )}
      </motion.div>

      {/* Ripple Effect */}
      {!isOpen && (
        <motion.div
          className="absolute inset-0 rounded-full bg-blue-400"
          animate={{
            scale: [1, 1.5],
            opacity: [0.5, 0]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            repeatDelay: 1
          }}
        />
      )}
    </motion.button>
  );
}