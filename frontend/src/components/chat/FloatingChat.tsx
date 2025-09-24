import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, X } from 'lucide-react';
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

interface FloatingChatProps {
  isOpen: boolean;
  onClose: () => void;
}

const examplePrompts = [
  "Leg day nearby?",
  "Find chest equipment close to me",
  "Where can I do back exercises?",
  "What's available at Central branch?"
];

export default function FloatingChat({ isOpen, onClose }: FloatingChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hasLocation, setHasLocation] = useState(false);
  const [userLocation, setUserLocation] = useState<{ lat: number; lon: number } | null>(null);
  const [showLocationRequest, setShowLocationRequest] = useState(false);
  const [showInput, setShowInput] = useState(true);
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
      {/* Transparent overlay - only for closing */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-40"
        onClick={onClose}
      />

      {/* Floating Chat Bubbles Container */}
      <div className="fixed inset-0 z-50 pointer-events-none">
        <div className="flex flex-col h-full justify-end p-4 space-y-3">
          {/* Close Button */}
          <div className="flex justify-end pointer-events-auto">
            <motion.button
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              onClick={onClose}
              className="w-10 h-10 bg-white/90 backdrop-blur-sm rounded-full shadow-lg flex items-center justify-center text-gray-600 hover:text-gray-800 hover:bg-white transition-all"
            >
              <X className="w-5 h-5" />
            </motion.button>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto space-y-3 pointer-events-auto max-h-[60vh]">
            {/* Example Prompts */}
            {messages.length === 0 && !isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-2"
              >
                {examplePrompts.map((prompt, index) => (
                  <motion.button
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    onClick={() => handleSendMessage(prompt)}
                    className="block w-full text-left text-sm bg-white/90 backdrop-blur-sm hover:bg-white text-gray-700 px-4 py-3 rounded-2xl shadow-lg border border-gray-200/50 transition-all hover:shadow-xl"
                  >
                    {prompt}
                  </motion.button>
                ))}
              </motion.div>
            )}

            {/* Chat Messages */}
            {messages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="space-y-2"
              >
                <div className="backdrop-blur-sm">
                  <ChatBubble message={message} />
                </div>
                {message.recommendations && (
                  <div className="space-y-2">
                    {message.recommendations.map((rec, recIndex) => (
                      <motion.div
                        key={rec.branchId}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: recIndex * 0.1 }}
                        className="backdrop-blur-sm"
                      >
                        <BranchRecommendationCard recommendation={rec} />
                      </motion.div>
                    ))}
                  </div>
                )}
              </motion.div>
            ))}

            {/* Loading indicator */}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="bg-white/90 backdrop-blur-sm rounded-2xl px-4 py-3 shadow-lg border border-gray-200/50">
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
              <div className="pointer-events-auto">
                <LocationPermissionRequest
                  onGrant={handleLocationGranted}
                  onDeny={handleLocationDenied}
                />
              </div>
            )}
          </AnimatePresence>

          {/* Floating Input */}
          {showInput && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="pointer-events-auto"
            >
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 p-4">
                <div className="flex items-center gap-3">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Ask me anything about gym equipment..."
                    className="flex-1 px-4 py-3 border border-gray-200 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/50 backdrop-blur-sm"
                    disabled={isLoading}
                  />
                  <button
                    onClick={() => handleSendMessage()}
                    disabled={!inputMessage.trim() || isLoading}
                    className="w-11 h-11 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white rounded-full flex items-center justify-center transition-colors shadow-lg"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </>
  );
}