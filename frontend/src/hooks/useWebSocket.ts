/**
 * React Hook for WebSocket Integration
 * Provides easy access to real-time gym machine updates
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { websocketService, WebSocketMessage, WebSocketSubscriptions, MachineUpdate, UserAlert } from '../services/websocketService';

export interface UseWebSocketResult {
  isConnected: boolean;
  isConnecting: boolean;
  messages: WebSocketMessage[];
  machineUpdates: MachineUpdate[];
  userAlerts: UserAlert[];
  lastUpdate: WebSocketMessage | null;
  connect: (subscriptions?: WebSocketSubscriptions, userId?: string) => Promise<void>;
  disconnect: () => void;
  clearMessages: () => void;
  updateSubscriptions: (subscriptions: WebSocketSubscriptions, userId?: string) => Promise<void>;
}

export function useWebSocket(): UseWebSocketResult {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [lastUpdate, setLastUpdate] = useState<WebSocketMessage | null>(null);
  
  // Refs to store cleanup functions
  const messageUnsubscribeRef = useRef<(() => void) | null>(null);
  const connectionUnsubscribeRef = useRef<(() => void) | null>(null);

  // Separate machine updates and user alerts for easier filtering
  const machineUpdates = messages.filter(msg => msg.type === 'machine_update') as MachineUpdate[];
  const userAlerts = messages.filter(msg => msg.type === 'user_alert') as UserAlert[];

  // Connect to WebSocket
  const connect = useCallback(async (subscriptions?: WebSocketSubscriptions, userId?: string) => {
    try {
      setIsConnecting(true);
      await websocketService.connect(subscriptions, userId);
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      throw error;
    } finally {
      setIsConnecting(false);
    }
  }, []);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  // Update subscription preferences
  const updateSubscriptions = useCallback(async (subscriptions: WebSocketSubscriptions, userId?: string) => {
    try {
      setIsConnecting(true);
      await websocketService.updateSubscriptions(subscriptions, userId);
    } catch (error) {
      console.error('Failed to update WebSocket subscriptions:', error);
      throw error;
    } finally {
      setIsConnecting(false);
    }
  }, []);

  // Clear message history
  const clearMessages = useCallback(() => {
    setMessages([]);
    setLastUpdate(null);
  }, []);

  // Set up listeners on component mount
  useEffect(() => {
    // Subscribe to connection status changes
    connectionUnsubscribeRef.current = websocketService.onConnectionChange((connected) => {
      setIsConnected(connected);
      if (!connected) {
        setIsConnecting(false);
      }
    });

    // Subscribe to incoming messages
    messageUnsubscribeRef.current = websocketService.onMessage((message) => {
      setMessages(prev => {
        // Limit message history to last 100 messages to prevent memory leaks
        const newMessages = [...prev, message];
        return newMessages.slice(-100);
      });
      setLastUpdate(message);
    });

    // Cleanup function
    return () => {
      if (messageUnsubscribeRef.current) {
        messageUnsubscribeRef.current();
      }
      if (connectionUnsubscribeRef.current) {
        connectionUnsubscribeRef.current();
      }
    };
  }, []);

  return {
    isConnected,
    isConnecting,
    messages,
    machineUpdates,
    userAlerts,
    lastUpdate,
    connect,
    disconnect,
    clearMessages,
    updateSubscriptions
  };
}

/**
 * Hook specifically for machine status updates
 * Provides filtered machine updates with latest status per machine
 */
export function useMachineUpdates(subscriptions?: WebSocketSubscriptions, userId?: string) {
  const webSocket = useWebSocket();
  const [latestMachineStatus, setLatestMachineStatus] = useState<Record<string, MachineUpdate>>({});

  // Auto-connect on mount if subscriptions provided (disabled in development)
  useEffect(() => {
    if (subscriptions && !webSocket.isConnected && !webSocket.isConnecting) {
      // Skip WebSocket connection in development environment
      if (import.meta.env.DEV && import.meta.env.VITE_ENABLE_WEBSOCKET !== 'true') {
        console.log('WebSocket disabled in development mode');
        return;
      }
      webSocket.connect(subscriptions, userId).catch(console.error);
    }
  }, [subscriptions, userId, webSocket]);

  // Update latest machine status when new updates arrive
  useEffect(() => {
    if (webSocket.lastUpdate && webSocket.lastUpdate.type === 'machine_update') {
      const update = webSocket.lastUpdate as MachineUpdate;
      setLatestMachineStatus(prev => ({
        ...prev,
        [update.machineId]: update
      }));
    }
  }, [webSocket.lastUpdate]);

  return {
    ...webSocket,
    latestMachineStatus,
    getAllMachineStatuses: () => Object.values(latestMachineStatus),
    getMachineStatus: (machineId: string) => latestMachineStatus[machineId],
  };
}

/**
 * Hook specifically for user alerts
 * Provides filtered user alerts with notification capabilities
 */
export function useUserAlerts(userId?: string) {
  const webSocket = useWebSocket();
  const [unreadAlerts, setUnreadAlerts] = useState<UserAlert[]>([]);

  // Auto-connect for user alerts (disabled in development)
  useEffect(() => {
    if (userId && !webSocket.isConnected && !webSocket.isConnecting) {
      // Skip WebSocket connection in development environment
      if (import.meta.env.DEV && import.meta.env.VITE_ENABLE_WEBSOCKET !== 'true') {
        console.log('WebSocket disabled in development mode');
        return;
      }
      // Subscribe to all branches/categories for user alerts
      const alertSubscriptions: WebSocketSubscriptions = {
        branches: ['hk-central', 'hk-causeway'],
        categories: ['legs', 'chest', 'back']
      };
      webSocket.connect(alertSubscriptions, userId).catch(console.error);
    }
  }, [userId, webSocket]);

  // Track unread alerts
  useEffect(() => {
    if (webSocket.lastUpdate && webSocket.lastUpdate.type === 'user_alert') {
      const alert = webSocket.lastUpdate as UserAlert;
      setUnreadAlerts(prev => [...prev, alert]);
      
      // Optional: Show browser notification
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Gym Machine Available!', {
          body: alert.message,
          icon: '/gym-icon.png', // Add your gym icon
        });
      }
    }
  }, [webSocket.lastUpdate]);

  const markAllAsRead = useCallback(() => {
    setUnreadAlerts([]);
  }, []);

  const markAsRead = useCallback((alertId: string) => {
    setUnreadAlerts(prev => prev.filter(alert => alert.alertId !== alertId));
  }, []);

  return {
    ...webSocket,
    unreadAlerts,
    unreadCount: unreadAlerts.length,
    markAllAsRead,
    markAsRead,
  };
}