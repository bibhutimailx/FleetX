export interface Vehicle {
  id: number;
  vehicle_id: string;
  driver_name?: string;
  license_plate?: string;
  vehicle_type?: string;
  created_at?: string;
  updated_at?: string;
}

export interface VehicleLocation {
  vehicle_id: string;
  latitude: number;
  longitude: number;
  speed: number;
  heading: number;
  timestamp: string;
  driver_name?: string;
  license_plate?: string;
  vehicle_type?: string;
}

export interface GeofenceEvent {
  id: number;
  vehicle_id: string;
  event_type: 'enter' | 'exit';
  latitude: number;
  longitude: number;
  geofence_name: string;
  timestamp: string;
  notification_sent: boolean;
}

export interface ActivityLog {
  id: number;
  vehicle_id: string;
  activity_type: string;
  description: string;
  latitude?: number;
  longitude?: number;
  metadata?: string;
  timestamp: string;
}

export interface GeofenceStatus {
  vehicle_id: string;
  is_inside_geofence: boolean;
  distance_to_geofence: number;
  geofence_center: {
    latitude: number;
    longitude: number;
  };
  geofence_radius: number;
  current_location: {
    latitude: number;
    longitude: number;
    timestamp: string;
  };
}

export interface EventsSummary {
  summary_period_hours: number;
  geofence_events: {
    enters: number;
    exits: number;
    total: number;
  };
  activities_by_type: Record<string, number>;
  active_vehicles: number;
  generated_at: string;
}

export interface WebSocketMessage {
  type: 'initial_locations' | 'location_update' | 'event_notification';
  data: any;
  timestamp: number;
}

