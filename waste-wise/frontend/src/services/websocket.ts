import { io, Socket } from 'socket.io-client';
import { toast } from 'react-hot-toast';
import { useAuthStore } from '../store/authStore';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<Function>> = new Map();

  connect() {
    const token = useAuthStore.getState().tokens?.access;
    
    if (!token) {
      console.warn('No auth token available for WebSocket connection');
      return;
    }

    this.socket = io(WS_URL, {
      auth: {
        token,
      },
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      
      // Subscribe to relevant channels
      this.subscribe('sensor_updates');
      this.subscribe('alerts');
      this.subscribe('route_updates');
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, attempt to reconnect
        this.reconnect();
      }
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
      toast.error('Connection error. Please check your internet connection.');
    });

    // Handle sensor updates
    this.socket.on('sensor_update', (data) => {
      this.emit('sensor_update', data);
    });

    // Handle alerts
    this.socket.on('alert_notification', (data) => {
      this.emit('alert_notification', data);
      
      // Show toast notification for high severity alerts
      if (data.severity === 'high' || data.severity === 'critical') {
        toast.error(data.title, {
          duration: 5000,
        });
      }
    });

    // Handle route updates
    this.socket.on('route_update', (data) => {
      this.emit('route_update', data);
    });

    // Handle bin status changes
    this.socket.on('bin_status_change', (data) => {
      this.emit('bin_status_change', data);
    });

    // Handle vehicle location updates
    this.socket.on('vehicle_location', (data) => {
      this.emit('vehicle_location', data);
    });

    // Handle command responses
    this.socket.on('command_response', (data) => {
      this.emit('command_response', data);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.listeners.clear();
  }

  private reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      toast.error('Failed to reconnect to server. Please refresh the page.');
      return;
    }

    this.reconnectAttempts++;
    
    setTimeout(() => {
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      this.connect();
    }, this.reconnectDelay * this.reconnectAttempts);
  }

  subscribe(channel: string) {
    if (!this.socket) return;
    
    this.socket.emit('subscribe', { channel });
  }

  unsubscribe(channel: string) {
    if (!this.socket) return;
    
    this.socket.emit('unsubscribe', { channel });
  }

  // Send command to sensor
  sendCommand(sensorId: string, command: string, parameters?: any) {
    if (!this.socket) {
      toast.error('WebSocket not connected');
      return;
    }

    this.socket.emit('sensor_command', {
      sensor_id: sensorId,
      command,
      parameters,
    });
  }

  // Event listener management
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: Function) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.delete(callback);
    }
  }

  private emit(event: string, data: any) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket event handler for ${event}:`, error);
        }
      });
    }
  }

  // Get connection status
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  // Get socket instance (for advanced usage)
  getSocket(): Socket | null {
    return this.socket;
  }
}

// Create singleton instance
const wsService = new WebSocketService();

export default wsService;