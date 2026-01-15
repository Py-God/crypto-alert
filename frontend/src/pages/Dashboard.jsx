// src/pages/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import { alertsAPI } from '../api/alerts';
import { marketAPI } from '../api/market';
import { 
  Bell, 
  Plus, 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Bitcoin,
  LogOut,
  Search,
  Filter,
  Edit2,
  Trash2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Activity,
  X,
  RefreshCw
} from 'lucide-react';

const Dashboard = ({ user, logout, isConnected, priceUpdates, subscribe, unsubscribe }) => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAssetType, setSelectedAssetType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    triggered: 0,
    watchlist: 5
  });
  const [loadingPrices, setLoadingPrices] = useState(false);

  // Watchlist symbols for real-time tracking
  const [watchlist, setWatchlist] = useState([
    { symbol: 'BTC', displaySymbol: 'BTC', type: 'crypto', price: 0, change: 0 },
    { symbol: 'ETH', displaySymbol: 'ETH', type: 'crypto', price: 0, change: 0 },
    { symbol: 'AAPL', displaySymbol: 'AAPL', type: 'stock', price: 0, change: 0 },
    { symbol: 'GOOGL', displaySymbol: 'GOOGL', type: 'stock', price: 0, change: 0 },
    { symbol: 'TSLA', displaySymbol: 'TSLA', type: 'stock', price: 0, change: 0 }
  ]);

  useEffect(() => {
    loadAlerts();
    loadWatchlistPrices();
    
    // Subscribe to watchlist symbols
    if (subscribe && typeof subscribe === 'function') {
      watchlist.forEach(item => {
        subscribe(item.symbol);
      });
    }

    return () => {
      if (unsubscribe && typeof unsubscribe === 'function') {
        watchlist.forEach(item => {
          unsubscribe(item.symbol);
        });
      }
    };
  }, []);

  // Update prices from WebSocket
  useEffect(() => {
    if (priceUpdates && typeof priceUpdates === 'object') {
      setWatchlist(prev => 
        prev.map(item => {
          const update = priceUpdates[item.symbol];
          return update ? { ...item, price: update.price, change: update.change } : item;
        })
      );
    }
  }, [priceUpdates]);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const data = await alertsAPI.getAlerts();
      console.log('📊 Loaded alerts data:', data);
      
      // Backend returns data.alerts, not data.items
      const alertItems = data.alerts || data.items || [];
      console.log('📋 Alert items:', alertItems);
      console.log('🔢 Number of alerts:', alertItems.length);
      
      setAlerts(alertItems);
      
      // Calculate stats
      const activeCount = alertItems.filter(a => a.status === 'active').length;
      const triggeredCount = alertItems.filter(a => a.status === 'triggered').length;
      
      console.log(`✅ Stats - Total: ${alertItems.length}, Active: ${activeCount}, Triggered: ${triggeredCount}`);
      
      setStats({
        total: data.total || alertItems.length,
        active: activeCount,
        triggered: triggeredCount,
        watchlist: watchlist.length
      });
    } catch (error) {
      console.error('❌ Failed to load alerts:', error);
      console.error('Error details:', error.response?.data);
      // Show user-friendly error
      if (error.response?.status === 401) {
        console.error('Unauthorized - redirecting to login');
        logout();
      } else {
        setAlerts([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadWatchlistPrices = async () => {
    setLoadingPrices(true);
    try {
      const pricePromises = watchlist.map(async (item) => {
        try {
          const priceData = await marketAPI.getPrice(item.symbol, item.type);
          console.log(`✅ Loaded price for ${item.symbol}:`, priceData);
          
          return {
            ...item,
            price: priceData.price || 0,
            change: 0 // Backend doesn't return change yet, we can add this later
          };
        } catch (error) {
          console.error(`❌ Failed to load price for ${item.symbol}:`, error.response?.data || error.message);
          return item; // Keep existing data on error
        }
      });

      const updatedWatchlist = await Promise.all(pricePromises);
      setWatchlist(updatedWatchlist);
    } catch (error) {
      console.error('Failed to load watchlist prices:', error);
    } finally {
      setLoadingPrices(false);
    }
  };

  const handleDeleteAlert = async (id) => {
    if (!window.confirm('Are you sure you want to delete this alert?')) return;
    
    try {
      await alertsAPI.deleteAlert(id);
      
      // Remove from local state
      setAlerts(prev => prev.filter(a => a.id !== id));
      
      // Update stats
      const newAlerts = alerts.filter(a => a.id !== id);
      setStats(prev => ({
        ...prev,
        total: newAlerts.length,
        active: newAlerts.filter(a => a.status === 'active').length
      }));
      
      console.log('Successfully deleted alert:', id);
    } catch (error) {
      console.error('Failed to delete alert:', error);
      alert('Failed to delete alert. Please try again.');
    }
  };

  const handleCreateAlert = async (formData) => {
    try {
      const newAlert = await alertsAPI.createAlert({
        symbol: formData.symbol.toUpperCase(),
        asset_type: formData.assetType,
        alert_type: formData.alertType,
        target_price: parseFloat(formData.targetPrice),
        notify_email: formData.notifyEmail,
        notify_sms: formData.notifySms
      });
      
      console.log('Successfully created alert:', newAlert);
      
      // Reload alerts to get fresh data
      await loadAlerts();
      
      return newAlert;
    } catch (error) {
      console.error('Failed to create alert:', error);
      throw new Error(error.response?.data?.detail || 'Failed to create alert');
    }
  };

  const handleRefreshPrices = () => {
    loadWatchlistPrices();
  };

  // Safe filtering with fallback
  const filteredAlerts = Array.isArray(alerts) ? alerts.filter(alert => {
    const matchesType = selectedAssetType === 'all' || alert.asset_type === selectedAssetType;
    const matchesSearch = alert.symbol.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  }) : [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <Activity className="w-8 h-8 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900">Price Alert Dashboard</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              
              {/* User Menu */}
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{user?.username || 'User'}</p>
                  <p className="text-xs text-gray-500">{user?.email || 'user@example.com'}</p>
                </div>
                <button
                  onClick={logout}
                  className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Alerts"
            value={stats.total}
            icon={<Bell className="w-6 h-6 text-blue-600" />}
            color="blue"
          />
          <StatCard
            title="Active Alerts"
            value={stats.active}
            icon={<CheckCircle className="w-6 h-6 text-green-600" />}
            color="green"
          />
          <StatCard
            title="Triggered"
            value={stats.triggered}
            icon={<AlertCircle className="w-6 h-6 text-yellow-600" />}
            color="yellow"
          />
          <StatCard
            title="Watchlist"
            value={stats.watchlist}
            icon={<TrendingUp className="w-6 h-6 text-purple-600" />}
            color="purple"
          />
        </div>

        {/* Watchlist Section */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">Live Prices</h2>
            <button
              onClick={handleRefreshPrices}
              disabled={loadingPrices}
              className="flex items-center space-x-2 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loadingPrices ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {watchlist.map(item => (
              <PriceCard key={item.symbol} {...item} loading={loadingPrices} />
            ))}
          </div>
        </div>

        {/* Alerts Section */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">My Alerts</h2>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              <span>Create Alert</span>
            </button>
          </div>

          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by symbol..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Filter */}
            <div className="flex items-center space-x-2">
              <Filter className="w-5 h-5 text-gray-400" />
              <select
                value={selectedAssetType}
                onChange={(e) => setSelectedAssetType(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Types</option>
                <option value="crypto">Crypto</option>
                <option value="stock">Stocks</option>
              </select>
            </div>
          </div>

          {/* Alerts List */}
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-500 mt-4">Loading alerts...</p>
            </div>
          ) : filteredAlerts.length === 0 ? (
            <div className="text-center py-12">
              <Bell className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No alerts found</p>
              <p className="text-gray-400 text-sm mt-2">
                {alerts.length === 0 
                  ? 'Create your first alert to get started'
                  : 'Try adjusting your filters'
                }
              </p>
              {/* Debug Info */}
              <div className="mt-4 text-xs text-gray-400">
                <p>Total alerts in state: {alerts.length}</p>
                <p>Filtered alerts: {filteredAlerts.length}</p>
                <p>Selected filter: {selectedAssetType}</p>
                <p>Search query: "{searchQuery}"</p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredAlerts.map(alert => (
                <AlertRow
                  key={alert.id}
                  alert={alert}
                  onDelete={handleDeleteAlert}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Alert Modal */}
      {showCreateModal && (
        <CreateAlertModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateAlert}
        />
      )}
    </div>
  );
};

// Stat Card Component
const StatCard = ({ title, value, icon, color }) => {
  const colorClasses = {
    blue: 'bg-blue-50',
    green: 'bg-green-50',
    yellow: 'bg-yellow-50',
    purple: 'bg-purple-50'
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

// Price Card Component
const PriceCard = ({ symbol, displaySymbol, type, price, change, loading }) => {
  const isPositive = change >= 0;
  const hasChange = change !== 0 && change !== undefined;
  
  return (
    <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          {type === 'crypto' ? (
            <Bitcoin className="w-5 h-5 text-orange-500" />
          ) : (
            <DollarSign className="w-5 h-5 text-green-600" />
          )}
          <span className="font-bold text-gray-900">{displaySymbol || symbol}</span>
        </div>
        <span className="text-xs text-gray-500 uppercase">{type}</span>
      </div>
      
      <div className="mb-1">
        {loading ? (
          <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
        ) : (
          <p className="text-2xl font-bold text-gray-900">
            ${price > 0 ? price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '--'}
          </p>
        )}
      </div>
      
      {!loading && hasChange && price > 0 && (
        <div className={`flex items-center space-x-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
          {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          <span className="text-sm font-medium">
            {isPositive ? '+' : ''}{change.toFixed(2)}%
          </span>
        </div>
      )}
      
      {!loading && !hasChange && price > 0 && (
        <div className="text-xs text-gray-400">
          Real-time data
        </div>
      )}
    </div>
  );
};

// Alert Row Component
const AlertRow = ({ alert, onDelete }) => {
  const getAlertTypeColor = (type) => {
    return type === 'above' ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50';
  };

  const getStatusBadge = (status) => {
    const badges = {
      active: { color: 'bg-green-100 text-green-800', icon: <CheckCircle className="w-4 h-4" /> },
      triggered: { color: 'bg-yellow-100 text-yellow-800', icon: <AlertCircle className="w-4 h-4" /> },
      inactive: { color: 'bg-gray-100 text-gray-800', icon: <XCircle className="w-4 h-4" /> }
    };
    return badges[status] || badges.inactive;
  };

  const statusBadge = getStatusBadge(alert.status);

  return (
    <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all">
      <div className="flex items-center space-x-4 flex-1">
        {/* Symbol & Type */}
        <div className="flex items-center space-x-2">
          {alert.asset_type === 'crypto' ? (
            <Bitcoin className="w-6 h-6 text-orange-500" />
          ) : (
            <DollarSign className="w-6 h-6 text-green-600" />
          )}
          <div>
            <p className="font-bold text-gray-900">{alert.symbol}</p>
            <p className="text-xs text-gray-500 uppercase">{alert.asset_type}</p>
          </div>
        </div>

        {/* Alert Type */}
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${getAlertTypeColor(alert.alert_type)}`}>
          {alert.alert_type === 'above' ? '↑' : '↓'} {alert.alert_type}
        </div>

        {/* Prices */}
        <div className="flex items-center space-x-6">
          <div>
            <p className="text-xs text-gray-500">Target</p>
            <p className="font-semibold text-gray-900">${alert.target_price.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Current</p>
            <p className="font-semibold text-gray-900">${alert.current_price?.toLocaleString() || 'N/A'}</p>
          </div>
        </div>

        {/* Status */}
        <div className={`flex items-center space-x-1 px-3 py-1 rounded-full text-sm font-medium ${statusBadge.color}`}>
          {statusBadge.icon}
          <span className="capitalize">{alert.status}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center space-x-2">
        <button
          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          title="Edit"
        >
          <Edit2 className="w-5 h-5" />
        </button>
        <button
          onClick={() => onDelete(alert.id)}
          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          title="Delete"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

// Create Alert Modal Component
const CreateAlertModal = ({ onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    symbol: '',
    assetType: 'crypto',
    alertType: 'above',
    targetPrice: '',
    notifyEmail: true,
    notifySms: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.symbol || !formData.targetPrice) {
      setError('Please fill in all required fields');
      return;
    }

    if (parseFloat(formData.targetPrice) <= 0) {
      setError('Target price must be greater than 0');
      return;
    }

    setError('');
    setLoading(true);

    try {
      await onSubmit(formData);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create alert');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-gray-900">Create New Alert</h3>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {/* Symbol */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Symbol <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.symbol}
              onChange={(e) => setFormData({ ...formData, symbol: e.target.value.toUpperCase() })}
              placeholder="BTC, ETH, AAPL, etc."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent uppercase"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              For crypto, use format like BTCUSDT, ETHUSDT
            </p>
          </div>

          {/* Asset Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Asset Type
            </label>
            <select
              value={formData.assetType}
              onChange={(e) => setFormData({ ...formData, assetType: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="crypto">Cryptocurrency</option>
              <option value="stock">Stock</option>
            </select>
          </div>

          {/* Alert Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Alert When Price Goes
            </label>
            <select
              value={formData.alertType}
              onChange={(e) => setFormData({ ...formData, alertType: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="above">Above Target</option>
              <option value="below">Below Target</option>
            </select>
          </div>

          {/* Target Price */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Price ($) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.targetPrice}
              onChange={(e) => setFormData({ ...formData, targetPrice: e.target.value })}
              placeholder="45000.00"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {/* Notification Preferences */}
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">
              Notifications
            </label>
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={formData.notifyEmail}
                onChange={(e) => setFormData({ ...formData, notifyEmail: e.target.checked })}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label className="ml-2 text-sm text-gray-600">
                Email notifications
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={formData.notifySms}
                onChange={(e) => setFormData({ ...formData, notifySms: e.target.checked })}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label className="ml-2 text-sm text-gray-600">
                SMS notifications
              </label>
            </div>
          </div>

          {/* Actions */}
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Alert'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;