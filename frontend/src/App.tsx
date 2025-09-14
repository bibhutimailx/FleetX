import React, { useState, useEffect, useCallback } from 'react';
import { VehicleLocation, WebSocketMessage } from './types/vehicle';
import { vehicleApi } from './services/api';
import { websocketService } from './services/websocket';
import Map from './components/Map';
import VehicleList from './components/VehicleList';
import ActivityLog from './components/ActivityLog';
import Dashboard from './components/Dashboard';
import { Truck, Activity, BarChart3, Wifi, WifiOff, RefreshCw } from 'lucide-react';

const App: React.FC = () => {
  const [vehicles, setVehicles] = useState<VehicleLocation[]>([]);
  const [selectedVehicle, setSelectedVehicle] = useState<string | undefined>();
  const [activeTab, setActiveTab] = useState<'map' | 'dashboard' | 'activity'>('map');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Geofence configuration (this would typically come from backend config)
  const geofenceCenter: [number, number] = [40.7128, -74.0060]; // NYC coordinates as example
  const geofenceRadius = 100; // meters

  const fetchVehicles = useCallback(async () => {
    try {
      setError(null);
      const locations = await vehicleApi.getVehicleLocations(100);
      setVehicles(locations);
    } catch (err) {
      setError('Failed to fetch vehicle data');
      console.error('Error fetching vehicles:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'initial_locations':
      case 'location_update':
        if (Array.isArray(message.data)) {
          setVehicles(message.data);
          setError(null);
        }
        break;
      case 'event_notification':
        // Trigger refresh for activity components
        setRefreshTrigger(prev => prev + 1);
        // You could show toast notifications here
        console.log('Event notification:', message.data);
        break;
      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  }, []);

  useEffect(() => {
    // Initial data fetch
    fetchVehicles();

    // Setup WebSocket connection
    const setupWebSocket = async () => {
      try {
        await websocketService.connect();
        setWsConnected(true);
        websocketService.addListener(handleWebSocketMessage);
      } catch (error) {
        console.error('WebSocket connection failed:', error);
        setWsConnected(false);
        // Fallback to polling if WebSocket fails
        const interval = setInterval(fetchVehicles, 30000); // Poll every 30 seconds
        return () => clearInterval(interval);
      }
    };

    setupWebSocket();

    // Cleanup
    return () => {
      websocketService.removeListener(handleWebSocketMessage);
      websocketService.disconnect();
    };
  }, [fetchVehicles, handleWebSocketMessage]);

  const handleRefresh = () => {
    if (wsConnected) {
      websocketService.requestLocations();
    } else {
      fetchVehicles();
    }
    setRefreshTrigger(prev => prev + 1);
  };

  const TabButton: React.FC<{
    id: string;
    label: string;
    icon: React.ReactNode;
    active: boolean;
    onClick: () => void;
  }> = ({ id, label, icon, active, onClick }) => (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
        active
          ? 'bg-blue-600 text-white'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </button>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Fleet Management</h2>
          <p className="text-gray-600">Connecting to vehicle tracking system...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <Truck className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">Fleet Management</h1>
                <p className="text-sm text-gray-600">Real-time vehicle tracking</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Connection Status */}
              <div className="flex items-center gap-2">
                {wsConnected ? (
                  <Wifi className="w-5 h-5 text-green-600" />
                ) : (
                  <WifiOff className="w-5 h-5 text-red-600" />
                )}
                <span className="text-sm text-gray-600">
                  {wsConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {/* Refresh Button */}
              <button
                onClick={handleRefresh}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                title="Refresh data"
              >
                <RefreshCw className="w-5 h-5" />
              </button>

              {/* Vehicle Count */}
              <div className="text-sm text-gray-600">
                {vehicles.length} vehicle{vehicles.length !== 1 ? 's' : ''}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-2 py-4">
            <TabButton
              id="map"
              label="Map View"
              icon={<Truck className="w-5 h-5" />}
              active={activeTab === 'map'}
              onClick={() => setActiveTab('map')}
            />
            <TabButton
              id="dashboard"
              label="Dashboard"
              icon={<BarChart3 className="w-5 h-5" />}
              active={activeTab === 'dashboard'}
              onClick={() => setActiveTab('dashboard')}
            />
            <TabButton
              id="activity"
              label="Activity Log"
              icon={<Activity className="w-5 h-5" />}
              active={activeTab === 'activity'}
              onClick={() => setActiveTab('activity')}
            />
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between">
              <p className="text-red-700">{error}</p>
              <button
                onClick={handleRefresh}
                className="text-red-600 hover:text-red-800 font-medium text-sm"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'map' && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-200px)]">
            {/* Map */}
            <div className="lg:col-span-3 bg-white rounded-lg shadow overflow-hidden">
              <Map
                vehicles={vehicles}
                geofenceCenter={geofenceCenter}
                geofenceRadius={geofenceRadius}
                selectedVehicle={selectedVehicle}
                onVehicleSelect={setSelectedVehicle}
              />
            </div>

            {/* Vehicle List */}
            <div className="lg:col-span-1">
              <VehicleList
                vehicles={vehicles}
                selectedVehicle={selectedVehicle}
                onVehicleSelect={setSelectedVehicle}
                geofenceCenter={geofenceCenter}
                geofenceRadius={geofenceRadius}
              />
            </div>
          </div>
        )}

        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <Dashboard refreshTrigger={refreshTrigger} />
          </div>
        )}

        {activeTab === 'activity' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <ActivityLog
                selectedVehicle={selectedVehicle}
                refreshTrigger={refreshTrigger}
              />
            </div>
            <div className="lg:col-span-1">
              <VehicleList
                vehicles={vehicles}
                selectedVehicle={selectedVehicle}
                onVehicleSelect={setSelectedVehicle}
                geofenceCenter={geofenceCenter}
                geofenceRadius={geofenceRadius}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;

