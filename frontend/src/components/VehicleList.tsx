import React from 'react';
import { VehicleLocation } from '../types/vehicle';
import { Truck, Navigation, Clock, MapPin, User, Hash } from 'lucide-react';
import { format } from 'date-fns';

interface VehicleListProps {
  vehicles: VehicleLocation[];
  selectedVehicle?: string;
  onVehicleSelect: (vehicleId: string) => void;
  geofenceCenter: [number, number];
  geofenceRadius: number;
}

const VehicleList: React.FC<VehicleListProps> = ({
  vehicles,
  selectedVehicle,
  onVehicleSelect,
  geofenceCenter,
  geofenceRadius
}) => {
  const isVehicleInsideGeofence = (vehicle: VehicleLocation): boolean => {
    const distance = Math.sqrt(
      Math.pow((vehicle.latitude - geofenceCenter[0]) * 111000, 2) +
      Math.pow((vehicle.longitude - geofenceCenter[1]) * 111000, 2)
    );
    return distance <= geofenceRadius;
  };

  const formatSpeed = (speed: number): string => {
    return `${speed.toFixed(1)} km/h`;
  };

  const formatTimestamp = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      
      if (diffMinutes < 1) {
        return 'Just now';
      } else if (diffMinutes < 60) {
        return `${diffMinutes}m ago`;
      } else {
        return format(date, 'HH:mm');
      }
    } catch {
      return timestamp;
    }
  };

  const getStatusColor = (vehicle: VehicleLocation): string => {
    const timestamp = new Date(vehicle.timestamp);
    const now = new Date();
    const diffMinutes = (now.getTime() - timestamp.getTime()) / (1000 * 60);
    
    if (diffMinutes > 10) return 'bg-gray-400'; // Offline
    if (vehicle.speed > 80) return 'bg-red-500'; // Speeding
    if (isVehicleInsideGeofence(vehicle)) return 'bg-green-500'; // In geofence
    return 'bg-blue-500'; // Active
  };

  const sortedVehicles = [...vehicles].sort((a, b) => {
    // Sort by: selected first, then by timestamp (newest first)
    if (a.vehicle_id === selectedVehicle) return -1;
    if (b.vehicle_id === selectedVehicle) return 1;
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold">Vehicles ({vehicles.length})</h2>
        <p className="text-sm text-gray-600 mt-1">
          Real-time vehicle tracking and status
        </p>
      </div>

      <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
        {sortedVehicles.length === 0 ? (
          <div className="p-6 text-center">
            <Truck className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No vehicles found</p>
          </div>
        ) : (
          sortedVehicles.map((vehicle) => {
            const isInside = isVehicleInsideGeofence(vehicle);
            const isSelected = vehicle.vehicle_id === selectedVehicle;
            
            return (
              <div
                key={vehicle.vehicle_id}
                className={`p-4 cursor-pointer transition-colors duration-200 hover:bg-gray-50 ${
                  isSelected ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                }`}
                onClick={() => onVehicleSelect(vehicle.vehicle_id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="relative">
                      <Truck className="w-6 h-6 text-gray-600" />
                      <div 
                        className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${getStatusColor(vehicle)}`}
                      />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-gray-900">
                          Vehicle {vehicle.vehicle_id}
                        </h3>
                        <div className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          isInside 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {isInside ? 'In Zone' : 'Out Zone'}
                        </div>
                      </div>
                      
                      <div className="space-y-1 text-sm text-gray-600">
                        {vehicle.driver_name && (
                          <div className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            <span className="truncate">{vehicle.driver_name}</span>
                          </div>
                        )}
                        
                        {vehicle.license_plate && (
                          <div className="flex items-center gap-1">
                            <Hash className="w-3 h-3" />
                            <span>{vehicle.license_plate}</span>
                          </div>
                        )}
                        
                        <div className="flex items-center gap-1">
                          <Navigation className="w-3 h-3" />
                          <span>{formatSpeed(vehicle.speed)}</span>
                        </div>
                        
                        <div className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          <span className="truncate">
                            {vehicle.latitude.toFixed(4)}, {vehicle.longitude.toFixed(4)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                      <Clock className="w-3 h-3" />
                      {formatTimestamp(vehicle.timestamp)}
                    </div>
                    
                    {vehicle.vehicle_type && (
                      <div className="text-xs text-gray-400 mt-1">
                        {vehicle.vehicle_type}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
      
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>In Zone</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              <span>Speeding</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
              <span>Offline</span>
            </div>
          </div>
          
          <div className="text-xs">
            Last updated: {formatTimestamp(new Date().toISOString())}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VehicleList;

