import React, { useState, useEffect } from 'react';
import { EventsSummary } from '../types/vehicle';
import { eventsApi } from '../services/api';
import { Activity, TrendingUp, AlertTriangle, Users, MapPin, Clock } from 'lucide-react';
import { format } from 'date-fns';

interface DashboardProps {
  refreshTrigger?: number;
}

const Dashboard: React.FC<DashboardProps> = ({ refreshTrigger }) => {
  const [summary, setSummary] = useState<EventsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeFilter, setTimeFilter] = useState(24);

  useEffect(() => {
    fetchSummary();
  }, [timeFilter, refreshTrigger]);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await eventsApi.getEventsSummary(timeFilter);
      setSummary(data);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Error fetching summary:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-6">Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="animate-pulse">
              <div className="h-24 bg-gray-200 rounded-lg"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Dashboard</h2>
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-700">{error || 'No data available'}</p>
          <button
            onClick={fetchSummary}
            className="mt-2 text-sm text-red-600 hover:text-red-800 font-medium"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    icon: React.ReactNode;
    color: string;
    subtitle?: string;
  }> = ({ title, value, icon, color, subtitle }) => (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-center">
        <div className={`p-2 rounded-lg ${color}`}>
          {icon}
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500">{subtitle}</p>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">Dashboard</h2>
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
        <p className="text-sm text-gray-600 mt-1">
          Fleet overview for the last {timeFilter} hours
        </p>
      </div>

      <div className="p-6">
        {/* Main Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard
            title="Active Vehicles"
            value={summary.active_vehicles}
            icon={<Users className="w-5 h-5 text-white" />}
            color="bg-blue-500"
          />
          
          <StatCard
            title="Zone Entries"
            value={summary.geofence_events.enters}
            icon={<MapPin className="w-5 h-5 text-white" />}
            color="bg-green-500"
          />
          
          <StatCard
            title="Zone Exits"
            value={summary.geofence_events.exits}
            icon={<TrendingUp className="w-5 h-5 text-white" />}
            color="bg-red-500"
          />
          
          <StatCard
            title="Total Events"
            value={summary.geofence_events.total}
            icon={<Activity className="w-5 h-5 text-white" />}
            color="bg-purple-500"
          />
        </div>

        {/* Activity Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Activity Types */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-4">Activity Breakdown</h3>
            {Object.keys(summary.activities_by_type).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(summary.activities_by_type).map(([type, count]) => (
                  <div key={type} className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      {type === 'geofence_enter' && <MapPin className="w-4 h-4 text-green-600" />}
                      {type === 'geofence_exit' && <TrendingUp className="w-4 h-4 text-red-600" />}
                      {type === 'speed_alert' && <AlertTriangle className="w-4 h-4 text-yellow-600" />}
                      {!['geofence_enter', 'geofence_exit', 'speed_alert'].includes(type) && 
                        <Activity className="w-4 h-4 text-blue-600" />}
                      <span className="text-sm font-medium capitalize">
                        {type.replace('_', ' ')}
                      </span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">{count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No activities recorded</p>
            )}
          </div>

          {/* Summary Info */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-4">Summary</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Reporting Period</span>
                <span className="text-sm font-medium">{summary.summary_period_hours} hours</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Geofence Activity</span>
                <span className="text-sm font-medium">
                  {summary.geofence_events.total} events
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Entry Rate</span>
                <span className="text-sm font-medium">
                  {summary.geofence_events.total > 0 
                    ? Math.round((summary.geofence_events.enters / summary.geofence_events.total) * 100)
                    : 0}%
                </span>
              </div>
              
              <div className="pt-3 border-t border-gray-200">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <Clock className="w-3 h-3" />
                  <span>
                    Last updated: {format(new Date(summary.generated_at), 'MMM dd, HH:mm:ss')}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="border-t border-gray-200 px-6 py-3">
        <button
          onClick={fetchSummary}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          Refresh Dashboard
        </button>
      </div>
    </div>
  );
};

export default Dashboard;

