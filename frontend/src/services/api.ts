import axios from 'axios';
import { Vehicle, VehicleLocation, GeofenceEvent, ActivityLog, GeofenceStatus, EventsSummary } from '../types/vehicle';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const vehicleApi = {
  // Get all vehicles
  getVehicles: async (): Promise<Vehicle[]> => {
    const response = await api.get('/vehicles/');
    return response.data.vehicles;
  },

  // Get vehicle locations
  getVehicleLocations: async (limit: number = 100, vehicleId?: string): Promise<VehicleLocation[]> => {
    const params: any = { limit };
    if (vehicleId) params.vehicle_id = vehicleId;
    
    const response = await api.get('/vehicles/locations', { params });
    return response.data.locations;
  },

  // Get specific vehicle location
  getVehicleLocation: async (vehicleId: string): Promise<VehicleLocation> => {
    const response = await api.get(`/vehicles/${vehicleId}/location`);
    return response.data;
  },

  // Get vehicle location history
  getVehicleHistory: async (vehicleId: string, hours: number = 24): Promise<VehicleLocation[]> => {
    const response = await api.get(`/vehicles/${vehicleId}/history`, {
      params: { hours }
    });
    return response.data.history;
  },

  // Get vehicle geofence status
  getVehicleGeofenceStatus: async (vehicleId: string): Promise<GeofenceStatus> => {
    const response = await api.get(`/vehicles/${vehicleId}/geofence-status`);
    return response.data;
  },
};

export const eventsApi = {
  // Get geofence events
  getGeofenceEvents: async (
    hours: number = 24,
    vehicleId?: string,
    eventType?: 'enter' | 'exit'
  ): Promise<GeofenceEvent[]> => {
    const params: any = { hours };
    if (vehicleId) params.vehicle_id = vehicleId;
    if (eventType) params.event_type = eventType;

    const response = await api.get('/events/geofence', { params });
    return response.data.events;
  },

  // Get activity log
  getActivityLog: async (
    hours: number = 24,
    vehicleId?: string,
    activityType?: string,
    limit: number = 100
  ): Promise<ActivityLog[]> => {
    const params: any = { hours, limit };
    if (vehicleId) params.vehicle_id = vehicleId;
    if (activityType) params.activity_type = activityType;

    const response = await api.get('/events/activity', { params });
    return response.data.activities;
  },

  // Get events summary
  getEventsSummary: async (hours: number = 24): Promise<EventsSummary> => {
    const response = await api.get('/events/summary', {
      params: { hours }
    });
    return response.data;
  },
};

export const healthApi = {
  // Health check
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;

