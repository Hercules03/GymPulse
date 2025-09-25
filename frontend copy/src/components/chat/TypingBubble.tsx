import React from 'react';
import { motion } from 'framer-motion';

interface TypingBubbleProps {
  onClick: () => void;
  className?: string;
}

export default function TypingBubble({ onClick, className = '' }: TypingBubbleProps) {
  return (
    <motion.button
      onClick={onClick}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`
        relative bg-white rounded-full px-4 py-3 md:px-6 md:py-4 shadow-lg border border-gray-200
        hover:shadow-xl hover:bg-gray-50 transition-all duration-300
        flex items-center gap-2 md:gap-3 cursor-pointer
        ${className}
      `}
    >
      {/* Typing Dots Animation */}
      <div className="flex items-center gap-1">
        <motion.div
          className="w-2 h-2 bg-blue-500 rounded-full"
          animate={{
            y: [0, -4, 0],
            opacity: [0.4, 1, 0.4]
          }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            delay: 0
          }}
        />
        <motion.div
          className="w-2 h-2 bg-blue-500 rounded-full"
          animate={{
            y: [0, -4, 0],
            opacity: [0.4, 1, 0.4]
          }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            delay: 0.2
          }}
        />
        <motion.div
          className="w-2 h-2 bg-blue-500 rounded-full"
          animate={{
            y: [0, -4, 0],
            opacity: [0.4, 1, 0.4]
          }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            delay: 0.4
          }}
        />
      </div>

      {/* Text */}
      <div className="text-left">
        <div className="text-sm md:text-base font-medium text-gray-800">
          Which machines are you looking for?
        </div>
        <div className="text-xs md:text-sm text-gray-500 mt-0.5">
          Ask me to find the best gym for you
        </div>
      </div>

      {/* Subtle pulse animation for the entire bubble */}
      <motion.div
        className="absolute inset-0 rounded-full bg-blue-100"
        animate={{
          scale: [1, 1.05, 1],
          opacity: [0, 0.3, 0]
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          repeatDelay: 3
        }}
      />
    </motion.button>
  );
}