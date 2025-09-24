import { useState } from 'react';
import { motion } from 'framer-motion';
import { MessageCircle, Zap, MapPin, Users } from 'lucide-react';
import ChatInterface from './ChatInterface';
import FloatingChatButton from './FloatingChatButton';

export default function ChatDemo() {
  const [isChatOpen, setIsChatOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl mx-auto"
      >
        {/* Header */}
        <div className="text-center mb-12">
          <motion.h1 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl font-bold text-gray-900 mb-4"
          >
            GymPulse AI Assistant
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-xl text-gray-600 mb-8"
          >
            Your intelligent gym companion for finding available equipment nearby
          </motion.p>
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {[
            {
              icon: MessageCircle,
              title: "Natural Conversation",
              description: "Ask in plain English like 'Leg day nearby?'"
            },
            {
              icon: MapPin,
              title: "Location-Aware",
              description: "Finds gyms near you with travel times"
            },
            {
              icon: Users,
              title: "Live Availability",
              description: "Real-time equipment status updates"
            },
            {
              icon: Zap,
              title: "Smart Recommendations",
              description: "Ranked by ETA and equipment availability"
            }
          ].map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * index }}
              className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4">
                <feature.icon className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-sm text-gray-600">{feature.description}</p>
            </motion.div>
          ))}
        </div>

        {/* Demo Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white rounded-2xl p-8 shadow-lg text-center"
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Try the AI Assistant
          </h2>
          <p className="text-gray-600 mb-6">
            Click the chat button to start a conversation and experience the smart gym recommendations
          </p>
          
          <div className="flex flex-wrap justify-center gap-3 mb-6">
            {[
              "Leg day nearby?",
              "Find chest equipment close to me",
              "Where can I do back exercises?",
              "What's available at Central branch?"
            ].map((prompt) => (
              <span
                key={prompt}
                className="bg-blue-50 text-blue-700 px-4 py-2 rounded-full text-sm font-medium"
              >
                "{prompt}"
              </span>
            ))}
          </div>

          <button
            onClick={() => setIsChatOpen(true)}
            className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-8 py-3 rounded-xl font-medium transition-all transform hover:scale-105 flex items-center gap-2 mx-auto"
          >
            <MessageCircle className="w-5 h-5" />
            Start Chatting
          </button>
        </motion.div>
      </motion.div>

      {/* Chat Interface */}
      <FloatingChatButton 
        isOpen={isChatOpen}
        onClick={() => setIsChatOpen(!isChatOpen)}
      />
      
      <ChatInterface 
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  );
}