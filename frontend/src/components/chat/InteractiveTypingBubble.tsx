import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import ChatBubble from './ChatBubble';
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

interface InteractiveTypingBubbleProps {
  onToggle: (isOpen: boolean) => void;
  className?: string;
  userLocation?: { lat: number; lon: number } | null;
}

const examplePrompts = [
  "Leg day nearby?",
  "Find chest equipment close to me",
  "Where can I do back exercises?",
  "What's available at Central branch?"
];

export default function InteractiveTypingBubble({ onToggle, className = '', userLocation: propUserLocation }: InteractiveTypingBubbleProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    onToggle(isExpanded);
  }, [isExpanded, onToggle]);

  // Handle escape key to close chat
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isExpanded) {
        setIsExpanded(false);
      }
    };

    if (isExpanded) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isExpanded]);

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
                         message.toLowerCase().includes('near me') ||
                         message.toLowerCase().includes('where can i') ||
                         message.toLowerCase().includes('where to') ||
                         message.toLowerCase().includes('find') ||
                         message.toLowerCase().includes('leg day') ||
                         message.toLowerCase().includes('chest') ||
                         message.toLowerCase().includes('back') ||
                         message.toLowerCase().includes('exercises') ||
                         message.toLowerCase().includes('equipment');

    if (propUserLocation) {
      await processMessageWithLocation(message, propUserLocation);
    } else if (needsLocation) {
      // Show a message that location is being requested
      const locationMessage: Message = {
        id: Date.now().toString(),
        type: 'system',
        content: "📍 Location access is needed for personalized recommendations. Please allow location access when prompted by your browser.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, locationMessage]);
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



  return (
    <div className={`relative ${className}`}>
      {/* Chat Input with integrated prompts - Single container */}
      <div className="relative">
        {/* Example Prompts - Show above input when focused with no messages */}
        {isExpanded && messages.length === 0 && !isLoading && (
          <>
            {/* Prompts container */}
            <div className="absolute bottom-full left-0 right-0 mb-3 space-y-2 relative z-20">
              {examplePrompts.map((prompt, index) => (
                <button
                  key={index}
                  onClick={(e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    console.log('Prompt clicked:', prompt);
                    handleSendMessage(prompt);
                  }}
                  className="block w-full text-left text-sm bg-white/90 backdrop-blur-sm hover:bg-white text-gray-700 px-4 py-3 rounded-2xl shadow-lg border border-gray-200/50 hover:shadow-xl"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </>
        )}

        {/* Chat messages and loading - Show above input when there are messages */}
        {(messages.length > 0 || isLoading) && (
          <div className="absolute bottom-full left-0 right-0 mb-3 space-y-2 max-h-[60vh] overflow-y-auto flex flex-col-reverse">
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white/90 backdrop-blur-sm rounded-2xl px-4 py-3 shadow-lg border border-gray-200/50">
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}

            {/* Chat Messages - newest first */}
            {messages.slice().reverse().map((message) => (
              <div key={message.id} className="space-y-2">
                <div>
                  <ChatBubble message={message} />
                </div>
                {message.recommendations && (
                  <div className="space-y-2">
                    {message.recommendations.map((rec) => (
                      <div key={rec.branchId}>
                        <BranchRecommendationCard recommendation={rec} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}


        {/* Main typing bubble input */}
        <div className="bg-white rounded-2xl px-4 py-3 md:px-6 md:py-4 shadow-lg border border-gray-200 hover:shadow-xl hover:bg-gray-50 flex items-center gap-3 w-full relative z-10">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            onFocus={() => setIsExpanded(true)}
            onBlur={(e) => {
              // Only close if clicking outside the chat container and no message typed
              if (!inputMessage && !e.currentTarget.contains(e.relatedTarget as Node)) {
                setTimeout(() => setIsExpanded(false), 150);
              }
            }}
            placeholder={messages.length > 0 ? "Continue the conversation..." : "Ask me anything about gym equipment..."}
            className="flex-1 text-sm md:text-base text-gray-500 bg-transparent border-none outline-none placeholder-gray-500"
            disabled={isLoading}
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputMessage.trim() || isLoading}
            className="w-8 h-8 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white rounded-full flex items-center justify-center"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}