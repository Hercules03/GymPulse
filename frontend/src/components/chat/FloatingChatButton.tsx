import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { MessageCircle, X } from 'lucide-react';

interface FloatingChatButtonProps {
  isOpen: boolean;
  onClick: () => void;
  hasUnreadMessages?: boolean;
}

export default function FloatingChatButton({ isOpen, onClick, hasUnreadMessages = false }: FloatingChatButtonProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [dragConstraints, setDragConstraints] = useState({ top: 80, left: 20, right: 0, bottom: 0 });
  const constraintsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const updateConstraints = () => {
      setDragConstraints({
        top: 80, // Below header
        left: 20,
        right: window.innerWidth - 96, // Account for button width + padding
        bottom: window.innerHeight - 96
      });
    };

    updateConstraints();
    window.addEventListener('resize', updateConstraints);
    return () => window.removeEventListener('resize', updateConstraints);
  }, []);

  const handleDragStart = () => {
    setIsDragging(true);
  };

  const handleDragEnd = () => {
    // Small delay to prevent click event after drag
    setTimeout(() => setIsDragging(false), 100);
  };

  const handleClick = () => {
    if (!isDragging) {
      onClick();
    }
  };

  return (
    <>
      {/* Invisible constraints container */}
      <div ref={constraintsRef} className="fixed inset-0 pointer-events-none" />

      <motion.button
        drag
        dragMomentum={false}
        dragElastic={0.1}
        dragConstraints={constraintsRef}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onClick={handleClick}
        initial={{ scale: 0, opacity: 0 }}
        animate={{
          scale: 1,
          opacity: 1,
          y: 0 // No need to move up with popup dialog
        }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        whileHover={{ scale: isDragging ? 1 : 1.05 }}
        whileTap={{ scale: isDragging ? 1 : 0.95 }}
        className={`fixed bottom-4 right-4 z-50 w-14 h-14 rounded-full shadow-lg transition-all duration-300 flex items-center justify-center cursor-pointer ${
          isOpen
            ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            : 'bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700'
        } ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
        style={{ touchAction: 'none' }}
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
    </>
  );
}