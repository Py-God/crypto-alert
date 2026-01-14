// src/contexts/WebSocketContext.jsx
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';

const WebSocketContext = createContext(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [ws, setWs] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [priceUpdates, setPriceUpdates] = useState({});
  const [subscriptions, setSubscriptions] = useState([]);

  const connect = useCallback(() => {
    if (!isAuthenticated) return;

    const token = localStorage.getItem('access_token');
    if (!token) return;

    const websocket = new WebSocket(`ws://localhost:8000/api/v1/ws/connect?token=${token}`);

    websocket.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);

      setMessages((prev) => [...prev, data]);

      if (data.type === 'price_update') {
        setPriceUpdates((prev) => ({
          ...prev,
          [data.data.symbol]: data.data,
        }));
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (isAuthenticated) {
          connect();
        }
      }, 3000);
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      connect();
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [isAuthenticated, connect]);

  const subscribe = useCallback(
    (symbol) => {
      if (ws && isConnected) {
        ws.send(JSON.stringify({ type: 'subscribe', symbol }));
        setSubscriptions((prev) => [...new Set([...prev, symbol])]);
      }
    },
    [ws, isConnected]
  );

  const unsubscribe = useCallback(
    (symbol) => {
      if (ws && isConnected) {
        ws.send(JSON.stringify({ type: 'unsubscribe', symbol }));
        setSubscriptions((prev) => prev.filter((s) => s !== symbol));
      }
    },
    [ws, isConnected]
  );

  const sendMessage = useCallback(
    (message) => {
      if (ws && isConnected) {
        ws.send(JSON.stringify(message));
      }
    },
    [ws, isConnected]
  );

  const value = {
    isConnected,
    messages,
    priceUpdates,
    subscriptions,
    subscribe,
    unsubscribe,
    sendMessage,
  };

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
};