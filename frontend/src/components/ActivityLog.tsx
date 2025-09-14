import React, { useState, useEffect } from 'react';
import { ActivityLog as ActivityLogType, GeofenceEvent } from '../types/vehicle';
import { eventsApi } from '../services/api';
import { Clock, MapPin, AlertTriangle, LogIn, LogOut, Truck } from 'lucide-react';
import { format } from 'date-fns';

interface ActivityLogProps {
  selectedVehicle?: string;
  refreshTrigger?: number;
}

const ActivityLog: React.FC<ActivityLogProps> = ({ selectedVehicle, refreshTrigger }) => {
  const [activities, setActivities] = useState<ActivityLogType[]>([]);
  const [geofenceEvents, setGeofenceEvents] = useState<GeofenceEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeFilter, setTimeFilter] = useState(24); // hours

  useEffect(() => {
    fetchActivityData();
  }, [selectedVehicle, timeFilter, refreshTrigger]);

  const fetchActivityData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [activitiesData, eventsData] = await Promise.all([
        eventsApi.getActivityLog(timeFilter, selectedVehicle, undefined, 50),
        eventsApi.getGeofenceEvents(timeFilter, selectedVehicle)
      ]);

      setActivities(activitiesData);
      setGeofenceEvents(eventsData);
    } catch (err) {
      setError('Failed to load activity data');
      console.error('Error fetching activity data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getActivityIcon = (activityType: string) => {
    switch (activityType) {
      case 'geofence_enter':
        return <LogIn className="w-4 h-4 text-green-600" />;
      case 'geofence_exit':
        return <LogOut className="w-4 h-4 text-red-600" />;
      case 'speed_alert':
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      default:
        return <Truck className="w-4 h-4 text-blue-600" />;
    }
  };

  const getActivityColor = (activityType: string) => {
    switch (activityType) {
      case 'geofence_enter':
        return 'border-green-500 bg-green-50';
      case 'geofence_exit':
        return 'border-red-500 bg-red-50';
      case 'speed_alert':
        return 'border-yellow-500 bg-yellow-50';
      default:
        return 'border-blue-500 bg-blue-50';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'MMM dd, HH:mm:ss');
    } catch {
      return timestamp;
    }
  };

  const combinedActivities = [
    ...activities.map(activity => ({
      ...activity,
      type: 'activity' as const
    })),
    ...geofenceEvents.map(event => ({
      id: event.id,
      vehicle_id: event.vehicle_id,
      activity_type: `geofence_${event.event_type}`,
      description: `Vehicle ${event.vehicle_id} ${event.event_type === 'enter' ? 'entered' : 'exited'} ${event.geofence_name}`,
      latitude: event.latitude,
      longitude: event.longitude,
      timestamp: event.timestamp,
      type: 'geofence' as const
    }))
  ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Activity Log</h2>
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">Activity Log</h2>
          <select
            value={timeFilter}
            onChange={(e) => setTimeFilter(Number(e.target.value))}
            className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={1}>Last Hour</option>
            <option value={6}>Last 6 Hours</option>
            <option value={24}>Last 24 Hours</option>
            <option value={72}>Last 3 Days</option>
            <option value={168}>Last Week</option>
          </select>
        </div>
        
        {selectedVehicle && (
          <p className="text-sm text-gray-600 mt-1">
            Showing activities for Vehicle {selectedVehicle}
          </p>
        )}
      </div>

      <div className="activity-log p-4">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {combinedActivities.length === 0 ? (
          <div className="text-center py-8">
            <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No activities found for the selected period</p>
          </div>
        ) : (
          <div className="space-y-3">
            {combinedActivities.map((item, index) => (
              <div
                key={`${item.type}-${item.id}-${index}`}
                className={`activity-item border-l-4 pl-4 py-3 rounded-r-md ${getActivityColor(item.activity_type)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">
                      {getActivityIcon(item.activity_type)}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {item.description}
                      </p>
                      <div className="flex items-center gap-4 mt-1 text-xs text-gray-600">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatTimestamp(item.timestamp)}
                        </span>
                        {item.latitude && item.longitude && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {item.latitude.toFixed(4)}, {item.longitude.toFixed(4)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-xs text-gray-500 font-mono">
                    {item.vehicle_id}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-gray-200 px-4 py-3">
        <button
          onClick={fetchActivityData}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          Refresh Activity Log
        </button>
      </div>
    </div>
  );
};

export default ActivityLog;

