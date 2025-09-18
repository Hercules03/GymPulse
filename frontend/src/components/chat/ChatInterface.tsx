import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, MapPin, Clock, Users, X } from 'lucide-react';
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

interface ChatInterfaceProps {
  isOpen: boolean;
  onClose: () => void;
}

const examplePrompts = [
  "Leg day nearby?",
  "Find chest equipment close to me",
  "Where can I do back exercises?",
  "What's available at Central branch?"
];

// Bedrock agent handles category detection and intent parsing

export default function ChatInterface({ isOpen, onClose }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: "Hi! I'm your gym assistant. I can help you find available equipment nearby. Try asking me something like 'Leg day nearby?' 💪",
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hasLocation, setHasLocation] = useState(false);
  const [userLocation, setUserLocation] = useState<{ lat: number; lon: number } | null>(null);
  const [showLocationRequest, setShowLocationRequest] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

      // Convert recommendations from chat response to our format
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

    // Add user message only if not skipping (to avoid duplicates)
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

    // Check if location is needed
    const needsLocation = message.toLowerCase().includes('nearby') ||
                         message.toLowerCase().includes('close') ||
                         message.toLowerCase().includes('near me');

    console.log('🔍 Message processing debug:', {
      message,
      needsLocation,
      hasLocation,
      userLocation,
      skipUserMessage
    });

    if (needsLocation && !hasLocation && !userLocation) {
      console.log('🚨 Requesting location permission');
      setShowLocationRequest(true);
      return;
    }

    // Process message with location if we have it
    if (userLocation) {
      console.log('✅ Processing with user location:', userLocation);
      await processMessageWithLocation(message, userLocation);
    } else if (needsLocation) {
      // If location is needed but we don't have it, ask user to share location
      console.log('❌ Location needed but not available, asking user to grant location');
      setShowLocationRequest(true);
      return;
    } else {
      // Process without location
      setIsLoading(true);

      try {
        const chatRequest = {
          message: message,
          sessionId: 'default'
        };

        const chatResponse = await gymService.sendChatMessage(chatRequest);

        // Convert recommendations from chat response to our format
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
      // Get user's actual location
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const newLocation = {
              lat: position.coords.latitude,
              lon: position.coords.longitude
            };

            console.log('✅ Geolocation successful:', newLocation);

            // Set location state atomically
            setUserLocation(newLocation);
            setHasLocation(true);

            const systemMessage: Message = {
              id: Date.now().toString(),
              type: 'system',
              content: `Location access granted! 📍\nUsing coordinates: ${newLocation.lat.toFixed(4)}, ${newLocation.lon.toFixed(4)}\nNow I can find the closest gyms for you.`,
              timestamp: new Date()
            };
            setMessages(prev => [...prev, systemMessage]);

            // Continue with the original query
            const lastUserMessage = messages.filter(m => m.type === 'user').pop();
            if (lastUserMessage) {
              // Process the message directly with the new location
              processMessageWithLocation(lastUserMessage.content, newLocation);
            }
          },
          (error) => {
            console.error('❌ Geolocation error:', error.code, error.message);

            // Don't use fallback - instead inform user that location is required
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
            timeout: 10000, // 10 second timeout
            enableHighAccuracy: false, // Don't require GPS, allow network location
            maximumAge: 300000 // 5 minutes cache
          }
        );
      } else {
        // Browser doesn't support geolocation
        setShowLocationRequest(false);
        setIsLoading(false);

        const systemMessage: Message = {
          id: Date.now().toString(),
          type: 'assistant',
          content: "Your browser doesn't support location services. For nearby recommendations, please tell me which city or area you're in, or ask about specific gym branches.",
          timestamp: new Date()
        };
        setMessages(prev => [...prev, systemMessage]);
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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="fixed bottom-4 right-4 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden z-50"
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
            <Users className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="font-medium text-white">Gym Assistant</h3>
            <p className="text-blue-100 text-xs">Online</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-white/80 hover:text-white transition-colors p-1 rounded-full hover:bg-white/10"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="h-96 overflow-y-auto p-4 space-y-3">
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

      {/* Example Prompts */}
      {messages.length <= 1 && !isLoading && (
        <div className="px-4 py-2 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-2">Try asking:</p>
          <div className="flex flex-wrap gap-1">
            {examplePrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => handleSendMessage(prompt)}
                className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-gray-100 p-4">
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask about gym availability..."
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
  );
}