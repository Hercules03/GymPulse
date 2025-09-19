import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BarChart } from 'lucide-react';
import { AnimatePresence } from 'framer-motion';
import ChatInterface from '@/components/chat/ChatInterface';
import FloatingChatButton from '@/components/chat/FloatingChatButton';

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [isChatOpen, setIsChatOpen] = useState(false);

  return (
    <div className="min-h-screen w-full bg-gray-50">
      {/* Header with Logo */}
      <header className="bg-white border-b border-gray-100 py-4 sticky top-0 z-10">
        <div className="flex items-center justify-between px-6">
          <Link to="/branches" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
              <BarChart className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900 tracking-tight">GymPulse</span>
          </Link>

          {/* Navigation breadcrumb if on dashboard page */}
          {location.pathname.startsWith('/dashboard/') && (
            <nav className="flex items-center gap-2 text-sm text-gray-500">
              <Link to="/branches" className="hover:text-gray-700">Branches</Link>
              <span>/</span>
              <span className="text-gray-900">Dashboard</span>
            </nav>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Chat Interface */}
      <FloatingChatButton 
        isOpen={isChatOpen}
        onClick={() => setIsChatOpen(!isChatOpen)}
      />
      
      <AnimatePresence>
        <ChatInterface 
          isOpen={isChatOpen}
          onClose={() => setIsChatOpen(false)}
        />
      </AnimatePresence>
    </div>
  );
}