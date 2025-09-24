import React, { createContext, useContext, useState } from 'react';

interface ChatContextType {
  isChatOpen: boolean;
  setIsChatOpen: (open: boolean) => void;
  isBottomSheetOpen: boolean;
  setIsBottomSheetOpen: (open: boolean) => void;
  isFloatingChatOpen: boolean;
  setIsFloatingChatOpen: (open: boolean) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isBottomSheetOpen, setIsBottomSheetOpen] = useState(false);
  const [isFloatingChatOpen, setIsFloatingChatOpen] = useState(false);

  return (
    <ChatContext.Provider value={{
      isChatOpen,
      setIsChatOpen,
      isBottomSheetOpen,
      setIsBottomSheetOpen,
      isFloatingChatOpen,
      setIsFloatingChatOpen
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}