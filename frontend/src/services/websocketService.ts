/**
 * WebSocket Service for Real-Time Gym Machine Updates
 * Connects to AWS API Gateway WebSocket API for live status updates
 */

export interface MachineUpdate {
  type: 'machine_update';
  machineId: string;
  gymId: string;
  category: string;
  status: 'free' | 'occupied' | 'offline';
  timestamp: number;
  lastChange: number;
}

export interface UserAlert {
  type: 'user_alert';
  alertId: string;
  machineId: string;
  machineName: string;
  gymId: string;
  category: string;
  message: string;
  timestamp: number;
}

export type WebSocketMessage = MachineUpdate | UserAlert;

export interface WebSocketSubscriptions {
  branches?: string[];
  categories?: string[];
  machines?: string[];
}

class WebSocketService {
  private websocket: WebSocket | null = null;
  private connectionUrl: string;
  private isConnecting = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private messageListeners: ((message: WebSocketMessage) => void)[] = [];
  private connectionListeners: ((connected: boolean) => void)[] = [];
  private subscriptions: WebSocketSubscriptions = {};
  private mockUpdateInterval: NodeJS.Timeout | null = null;
  private isDevelopmentMode: boolean;

  constructor() {
    // Check if running in development mode with mock data
    this.isDevelopmentMode = import.meta.env.DEV && !import.meta.env.VITE_WEBSOCKET_URL;
    
    // Only set connection URL if WebSocket URL is actually configured
    this.connectionUrl = import.meta.env.VITE_WEBSOCKET_URL || '';
  }

  /**
   * Connect to WebSocket with optional subscription preferences
   */
  connect(subscriptions?: WebSocketSubscriptions, userId?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      // In development mode or when no WebSocket URL is configured, use mock updates
      if (this.isDevelopmentMode || !this.connectionUrl) {
        console.log('Development mode: Using mock WebSocket updates (no WebSocket URL configured)');
        this.startMockUpdates(subscriptions);
        this.notifyConnectionListeners(true);
        resolve();
        return;
      }

      if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        // Instead of rejecting, wait for the current connection attempt to complete
        const checkConnection = () => {
          if (!this.isConnecting) {
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
              resolve();
            } else {
              reject(new Error('Connection failed'));
            }
          } else {
            setTimeout(checkConnection, 100);
          }
        };
        setTimeout(checkConnection, 100);
        return;
      }

      this.isConnecting = true;
      this.subscriptions = subscriptions || {};

      // Build query parameters for subscription preferences
      const queryParams = new URLSearchParams();
      
      if (subscriptions?.branches?.length) {
        queryParams.set('branches', subscriptions.branches.join(','));
      }
      
      if (subscriptions?.categories?.length) {
        queryParams.set('categories', subscriptions.categories.join(','));
      }
      
      if (subscriptions?.machines?.length) {
        queryParams.set('machines', subscriptions.machines.join(','));
      }
      
      if (userId) {
        queryParams.set('userId', userId);
      }

      const wsUrl = `${this.connectionUrl}?${queryParams.toString()}`;
      
      try {
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
          console.log('WebSocket connected successfully');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000; // Reset delay
          this.notifyConnectionListeners(true);
          resolve();
        };

        this.websocket.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error, event.data);
          }
        };

        this.websocket.onclose = (event) => {
          console.log('WebSocket connection closed:', event.code, event.reason);
          this.isConnecting = false;
          this.websocket = null;
          this.notifyConnectionListeners(false);
          
          // Attempt reconnection if not a clean close
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnection();
          }
        };

        this.websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          
          if (this.reconnectAttempts === 0) {
            // First connection attempt failed
            reject(new Error('Failed to establish WebSocket connection'));
          }
        };

        // Connection timeout
        setTimeout(() => {
          if (this.isConnecting) {
            this.isConnecting = false;
            this.websocket?.close();
            reject(new Error('WebSocket connection timeout'));
          }
        }, 10000); // 10 second timeout

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.isDevelopmentMode) {
      this.stopMockUpdates();
      this.notifyConnectionListeners(false);
      return;
    }

    if (this.websocket) {
      this.websocket.close(1000, 'Client disconnect');
      this.websocket = null;
    }
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
    this.notifyConnectionListeners(false);
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    if (this.isDevelopmentMode) {
      return this.mockUpdateInterval !== null;
    }
    return this.websocket !== null && this.websocket.readyState === WebSocket.OPEN;
  }

  /**
   * Subscribe to message updates
   */
  onMessage(listener: (message: WebSocketMessage) => void): () => void {
    this.messageListeners.push(listener);
    
    // Return unsubscribe function
    return () => {
      const index = this.messageListeners.indexOf(listener);
      if (index > -1) {
        this.messageListeners.splice(index, 1);
      }
    };
  }

  /**
   * Subscribe to connection status changes
   */
  onConnectionChange(listener: (connected: boolean) => void): () => void {
    this.connectionListeners.push(listener);
    
    // Immediately notify of current connection status
    listener(this.isConnected());
    
    // Return unsubscribe function
    return () => {
      const index = this.connectionListeners.indexOf(listener);
      if (index > -1) {
        this.connectionListeners.splice(index, 1);
      }
    };
  }

  /**
   * Update subscription preferences (requires reconnection)
   */
  updateSubscriptions(subscriptions: WebSocketSubscriptions, userId?: string): Promise<void> {
    this.subscriptions = subscriptions;
    
    if (this.isConnected()) {
      // Reconnect with new subscriptions
      this.disconnect();
      return this.connect(subscriptions, userId);
    }
    
    return Promise.resolve();
  }

  private handleMessage(message: WebSocketMessage): void {
    console.log('Received WebSocket message:', message);
    
    // Validate message format
    if (!message.type) {
      console.warn('Received message without type:', message);
      return;
    }

    // Notify all listeners
    this.messageListeners.forEach(listener => {
      try {
        listener(message);
      } catch (error) {
        console.error('Error in message listener:', error);
      }
    });
  }

  private notifyConnectionListeners(connected: boolean): void {
    this.connectionListeners.forEach(listener => {
      try {
        listener(connected);
      } catch (error) {
        console.error('Error in connection listener:', error);
      }
    });
  }

  private scheduleReconnection(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Maximum reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000); // Max 30 seconds
    
    console.log(`Attempting WebSocket reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (this.reconnectAttempts <= this.maxReconnectAttempts && !this.isConnected()) {
        this.connect(this.subscriptions);
      }
    }, delay);
  }

  /**
   * Start mock updates for development mode
   */
  private startMockUpdates(subscriptions?: WebSocketSubscriptions): void {
    if (this.mockUpdateInterval) {
      clearInterval(this.mockUpdateInterval);
    }

    // Generate mock machine updates every 30 seconds
    this.mockUpdateInterval = setInterval(() => {
      const machines = [
        'leg-press-01', 'leg-press-02', 'squat-rack-01', 'calf-raise-01',
        'bench-press-01', 'bench-press-02', 'chest-fly-01',
        'lat-pulldown-01', 'rowing-01', 'pull-up-01'
      ];
      
      const categories = ['legs', 'chest', 'back'];
      const branches = ['hk-central', 'hk-causeway'];
      const statuses = ['free', 'occupied'] as const;
      
      // Generate a random update
      const randomMachine = machines[Math.floor(Math.random() * machines.length)];
      const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
      const randomCategory = categories[Math.floor(Math.random() * categories.length)];
      const randomBranch = branches[Math.floor(Math.random() * branches.length)];
      
      const mockUpdate: MachineUpdate = {
        type: 'machine_update',
        machineId: randomMachine,
        gymId: randomBranch,
        category: randomCategory,
        status: randomStatus,
        timestamp: Date.now(),
        lastChange: Date.now() - Math.random() * 300000 // Random time in last 5 minutes
      };
      
      this.handleMessage(mockUpdate);
    }, 30000); // Every 30 seconds
  }

  /**
   * Stop mock updates
   */
  private stopMockUpdates(): void {
    if (this.mockUpdateInterval) {
      clearInterval(this.mockUpdateInterval);
      this.mockUpdateInterval = null;
    }
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();