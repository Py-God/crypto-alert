// src/pages/DashboardWrapper.jsx
import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import Dashboard from './Dashboard';

const DashboardWrapper = () => {
  const { user, logout } = useAuth();
  const { isConnected, priceUpdates, subscribe, unsubscribe } = useWebSocket();

  return (
    <Dashboard
      user={user}
      logout={logout}
      isConnected={isConnected}
      priceUpdates={priceUpdates}
      subscribe={subscribe}
      unsubscribe={unsubscribe}
    />
  );
};

export default DashboardWrapper;