import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, X, ChevronDown, Maximize2, Minimize2 } from 'lucide-react';
import ChatBubble from './ChatBubble';
import LocationPermissionRequest from './LocationPermissionRequest';
import BranchRecommendationCard from './BranchRecommendationCard';
import { gymService } from '@/services/gymService';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  recommendations?: BranchRecommendation[];
}

interface BranchRecommendation {
  branchId: string;
  name: string;
  eta: string;
  distance: string;
  availableCount: number;
  totalCount: number;
  category: string;
}

interface BottomSheetChatProps {
  isOpen: boolean;
  onClose: () => void;
}

const examplePrompts = [
  "Leg day nearby?",
  "Find chest equipment close to me",
  "Where can I do back exercises?",
  "What's available at Central branch?"
];

export default function BottomSheetChat({ isOpen, onClose }: BottomSheetChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hasLocation, setHasLocation] = useState(false);
  const [userLocation, setUserLocation] = useState<{ lat: number; lon: number } | null>(null);
  const [showLocationRequest, setShowLocationRequest] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const processMessageWithLocation = async (message: string, location: { lat: number; lon: number }) => {
    console.log('🎯 processMessageWithLocation called:', { message, location });
    setIsLoading(true);

    try {
      const chatRequest = {
        message: message,
        userLocation: {
          lat: location.lat,
          lon: location.lon
        },
        sessionId: 'default'
      };

      console.log('📤 Sending chat request:', chatRequest);
      const chatResponse = await gymService.sendChatMessage(chatRequest);
      console.log('📥 Chat response received:', chatResponse);

      const recommendations: BranchRecommendation[] | undefined = chatResponse.recommendations?.map(rec => ({
        branchId: rec.branchId,
        name: rec.name,
        eta: rec.eta,
        distance: rec.distance,
        availableCount: rec.availableCount,
        totalCount: rec.totalCount,
        category: rec.category
      }));

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: chatResponse.response,
        timestamp: new Date(),
        recommendations
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error with chat API:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: "Sorry, I'm having trouble connecting to our chat system right now. Please try again in a moment!",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }

    setIsLoading(false);
  };

  const handleSendMessage = async (message: string = inputMessage, skipUserMessage = false) => {
    if (!message.trim()) return;

    if (!skipUserMessage) {
      const userMessage: Message = {
        id: Date.now().toString(),
        type: 'user',
        content: message,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);
      setInputMessage('');
    }

    const needsLocation = message.toLowerCase().includes('nearby') ||
                         message.toLowerCase().includes('close') ||
                         message.toLowerCase().includes('near me');

    if (needsLocation && !hasLocation && !userLocation) {
      setShowLocationRequest(true);
      return;
    }

    if (userLocation) {
      await processMessageWithLocation(message, userLocation);
    } else if (needsLocation) {
      setShowLocationRequest(true);
      return;
    } else {
      setIsLoading(true);

      try {
        const chatRequest = {
          message: message,
          sessionId: 'default'
        };

        const chatResponse = await gymService.sendChatMessage(chatRequest);

        const recommendations: BranchRecommendation[] | undefined = chatResponse.recommendations?.map(rec => ({
          branchId: rec.branchId,
          name: rec.name,
          eta: rec.eta,
          distance: rec.distance,
          availableCount: rec.availableCount,
          totalCount: rec.totalCount,
          category: rec.category
        }));

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: chatResponse.response,
          timestamp: new Date(),
          recommendations
        };

        setMessages(prev => [...prev, assistantMessage]);
      } catch (error) {
        console.error('Error with chat API:', error);
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: "Sorry, I'm having trouble connecting to our chat system right now. Please try again in a moment!",
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }

      setIsLoading(false);
    }
  };

  const handleLocationGranted = async () => {
    setShowLocationRequest(false);

    try {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const newLocation = {
              lat: position.coords.latitude,
              lon: position.coords.longitude
            };

            setUserLocation(newLocation);
            setHasLocation(true);

            const systemMessage: Message = {
              id: Date.now().toString(),
              type: 'system',
              content: `Location access granted! 📍\nUsing coordinates: ${newLocation.lat.toFixed(4)}, ${newLocation.lon.toFixed(4)}\nNow I can find the closest gyms for you.`,
              timestamp: new Date()
            };
            setMessages(prev => [...prev, systemMessage]);

            const lastUserMessage = messages.filter(m => m.type === 'user').pop();
            if (lastUserMessage) {
              processMessageWithLocation(lastUserMessage.content, newLocation);
            }
          },
          (error) => {
            console.error('❌ Geolocation error:', error.code, error.message);
            setShowLocationRequest(false);
            setIsLoading(false);

            const systemMessage: Message = {
              id: Date.now().toString(),
              type: 'assistant',
              content: `Unable to get your location (Error: ${error.message}). For nearby recommendations, I need your location. Please try allowing location access again, or ask about specific gym branches instead.`,
              timestamp: new Date()
            };
            setMessages(prev => [...prev, systemMessage]);
          },
          {
            timeout: 10000,
            enableHighAccuracy: false,
            maximumAge: 300000
          }
        );
      }
    } catch (error) {
      console.error('Error handling location grant:', error);
      setIsLoading(false);
    }
  };

  const handleLocationDenied = () => {
    setShowLocationRequest(false);

    const systemMessage: Message = {
      id: Date.now().toString(),
      type: 'assistant',
      content: "No problem! I can still help you find equipment at specific branches. Which gym location would you like to check?",
      timestamp: new Date()
    };
    setMessages(prev => [...prev, systemMessage]);
    setIsLoading(false);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-25 z-40 lg:hidden"
        onClick={onClose}
      />

      {/* Mobile Bottom Sheet */}
      <motion.div
        initial={{ y: '100%' }}
        animate={{
          y: 0,
          height: isExpanded ? '85vh' : '60vh'
        }}
        exit={{ y: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white rounded-t-2xl shadow-2xl flex flex-col overflow-hidden"
      >
        {/* Drag Handle & Header */}
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-4 py-3">
          {/* Drag Handle */}
          <div className="flex justify-center mb-2">
            <div className="w-10 h-1 bg-white/30 rounded-full" />
          </div>

          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-white">Gym Assistant</h3>
              <p className="text-blue-100 text-xs">Ask me to find the best gym for you</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-white/80 hover:text-white transition-colors p-1 rounded-full hover:bg-white/10"
              >
                {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </button>
              <button
                onClick={onClose}
                className="text-white/80 hover:text-white transition-colors p-1 rounded-full hover:bg-white/10"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
          {messages.length === 0 && !isLoading && (
            <div className="text-center py-8">
              <p className="text-gray-500 text-sm mb-4">Start by asking about gym equipment!</p>
              <div className="space-y-2">
                {examplePrompts.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => handleSendMessage(prompt)}
                    className="block w-full text-sm bg-white hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg border border-gray-200 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div key={message.id}>
              <ChatBubble message={message} />
              {message.recommendations && (
                <div className="mt-3 space-y-2">
                  {message.recommendations.map((rec, index) => (
                    <motion.div
                      key={rec.branchId}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <BranchRecommendationCard recommendation={rec} />
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="bg-gray-100 rounded-2xl px-4 py-3 max-w-[80%]">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Location Permission Request */}
        <AnimatePresence>
          {showLocationRequest && (
            <LocationPermissionRequest
              onGrant={handleLocationGranted}
              onDeny={handleLocationDenied}
            />
          )}
        </AnimatePresence>

        {/* Input */}
        <div className="border-t border-gray-100 p-4 bg-white">
          <div className="flex items-center gap-3">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Which machines are you looking for?"
              className="flex-1 px-4 py-3 border border-gray-200 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={!inputMessage.trim() || isLoading}
              className="w-11 h-11 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white rounded-full flex items-center justify-center transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </motion.div>

      {/* Desktop Side Panel */}
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="hidden lg:block fixed top-20 right-0 bottom-0 w-96 z-50 bg-white shadow-2xl border-l border-gray-200 flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-white">Gym Assistant</h3>
              <p className="text-blue-100 text-xs">Ask me to find the best gym for you</p>
            </div>
            <button
              onClick={onClose}
              className="text-white/80 hover:text-white transition-colors p-1 rounded-full hover:bg-white/10"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
          {messages.length === 0 && !isLoading && (
            <div className="text-center py-8">
              <p className="text-gray-500 text-sm mb-4">Start by asking about gym equipment!</p>
              <div className="space-y-2">
                {examplePrompts.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => handleSendMessage(prompt)}
                    className="block w-full text-sm bg-white hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg border border-gray-200 transition-colors text-left"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div key={message.id}>
              <ChatBubble message={message} />
              {message.recommendations && (
                <div className="mt-3 space-y-2">
                  {message.recommendations.map((rec, index) => (
                    <motion.div
                      key={rec.branchId}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <BranchRecommendationCard recommendation={rec} />
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="bg-gray-100 rounded-2xl px-4 py-3 max-w-[80%]">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Location Permission Request */}
        <AnimatePresence>
          {showLocationRequest && (
            <LocationPermissionRequest
              onGrant={handleLocationGranted}
              onDeny={handleLocationDenied}
            />
          )}
        </AnimatePresence>

        {/* Input */}
        <div className="border-t border-gray-100 p-4 bg-white">
          <div className="flex items-center gap-3">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Which machines are you looking for?"
              className="flex-1 px-4 py-2 border border-gray-200 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={!inputMessage.trim() || isLoading}
              className="w-9 h-9 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white rounded-full flex items-center justify-center transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.div>
    </>
  );
}