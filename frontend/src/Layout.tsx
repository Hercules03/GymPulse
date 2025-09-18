import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { createPageUrl } from '@/utils';
import { LayoutDashboard, Map, BarChart, FlaskConical } from 'lucide-react';
import { AnimatePresence } from 'framer-motion';
import ChatInterface from '@/components/chat/ChatInterface';
import FloatingChatButton from '@/components/chat/FloatingChatButton';

const navItems = [
  { name: 'Dashboard', href: createPageUrl('Dashboard'), icon: LayoutDashboard },
  { name: 'Branches', href: createPageUrl('Branches'), icon: Map },
  { name: 'ML Testing', href: createPageUrl('ml-validation'), icon: FlaskConical },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [isChatOpen, setIsChatOpen] = useState(false);

  return (
    <div className="min-h-screen w-full bg-gray-50 flex">
      {/* Sidebar Navigation */}
      <aside className="w-20 lg:w-64 bg-white border-r border-gray-100 flex flex-col">
        <div className="h-20 flex items-center justify-center lg:justify-start lg:px-6 shrink-0">
          <Link to={createPageUrl('Dashboard')} className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
              <BarChart className="w-5 h-5 text-white" />
            </div>
            <span className="hidden lg:block text-xl font-bold text-gray-900 tracking-tight">GymPulse</span>
          </Link>
        </div>
        <nav className="flex-1 px-4 py-6">
          <ul className="space-y-2">
            {navItems.map((item) => (
              <li key={item.name}>
                <Link
                  to={item.href}
                  className={`flex items-center gap-3 p-3 rounded-lg transition-colors
                    ${location.pathname === item.href
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                >
                  <item.icon className="w-5 h-5 shrink-0" />
                  <span className="hidden lg:block font-medium">{item.name}</span>
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>

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