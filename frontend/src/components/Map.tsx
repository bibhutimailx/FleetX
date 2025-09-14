import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import { Icon, LatLngTuple } from 'leaflet';
import { VehicleLocation } from '../types/vehicle';
import { Truck, Navigation, Clock } from 'lucide-react';
import { format } from 'date-fns';

interface MapProps {
  vehicles: VehicleLocation[];
  geofenceCenter: LatLngTuple;
  geofenceRadius: number;
  selectedVehicle?: string;
  onVehicleSelect?: (vehicleId: string) => void;
}

// Create custom vehicle icon
const createVehicleIcon = (isInsideGeofence: boolean, isSelected: boolean) => {
  const color = isInsideGeofence ? '#10b981' : '#ef4444';
  const size = isSelected ? 32 : 24;
  
  return new Icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(`
      <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" fill="white" stroke="${color}" stroke-width="2"/>
        <path d="M3 9h18v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9z" fill="${color}"/>
        <path d="M3 9V7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2" stroke="${color}" stroke-width="1" fill="none"/>
        <circle cx="8" cy="17" r="1" fill="${color}"/>
        <circle cx="16" cy="17" r="1" fill="${color}"/>
      </svg>
    `)}`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
};

// Create geofence center icon
const geofenceIcon = new Icon({
  iconUrl: `data:image/svg+xml;base64,${btoa(`
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" fill="#3b82f6" stroke="white" stroke-width="2"/>
      <path d="M12 6v6l4 2" stroke="white" stroke-width="2" stroke-linecap="round"/>
    </svg>
  `)}`,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
  popupAnchor: [0, -16],
});

const Map: React.FC<MapProps> = ({
  vehicles,
  geofenceCenter,
  geofenceRadius,
  selectedVehicle,
  onVehicleSelect
}) => {
  const [mapCenter, setMapCenter] = useState<LatLngTuple>(geofenceCenter);

  useEffect(() => {
    if (vehicles.length > 0 && !selectedVehicle) {
      // Center map on geofence if no vehicle is selected
      setMapCenter(geofenceCenter);
    } else if (selectedVehicle) {
      // Center map on selected vehicle
      const vehicle = vehicles.find(v => v.vehicle_id === selectedVehicle);
      if (vehicle) {
        setMapCenter([vehicle.latitude, vehicle.longitude]);
      }
    }
  }, [vehicles, selectedVehicle, geofenceCenter]);

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
      return format(new Date(timestamp), 'MMM dd, HH:mm:ss');
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="h-full w-full">
      <MapContainer
        center={mapCenter}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
        className="rounded-lg"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Geofence circle */}
        <Circle
          center={geofenceCenter}
          radius={geofenceRadius}
          pathOptions={{
            color: '#3b82f6',
            fillColor: '#3b82f6',
            fillOpacity: 0.1,
            weight: 2,
          }}
        />
        
        {/* Geofence center marker */}
        <Marker position={geofenceCenter} icon={geofenceIcon}>
          <Popup>
            <div className="p-2">
              <h3 className="font-semibold text-lg mb-2">Plant Gate</h3>
              <p className="text-sm text-gray-600">
                Geofence Center<br/>
                Radius: {geofenceRadius}m
              </p>
            </div>
          </Popup>
        </Marker>
        
        {/* Vehicle markers */}
        {vehicles.map((vehicle) => {
          const isInside = isVehicleInsideGeofence(vehicle);
          const isSelected = vehicle.vehicle_id === selectedVehicle;
          
          return (
            <Marker
              key={vehicle.vehicle_id}
              position={[vehicle.latitude, vehicle.longitude]}
              icon={createVehicleIcon(isInside, isSelected)}
              eventHandlers={{
                click: () => onVehicleSelect?.(vehicle.vehicle_id)
              }}
            >
              <Popup>
                <div className="p-3 min-w-[250px]">
                  <div className="flex items-center gap-2 mb-3">
                    <Truck className="w-5 h-5 text-blue-600" />
                    <h3 className="font-semibold text-lg">
                      Vehicle {vehicle.vehicle_id}
                    </h3>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    {vehicle.driver_name && (
                      <div>
                        <span className="font-medium">Driver:</span> {vehicle.driver_name}
                      </div>
                    )}
                    
                    {vehicle.license_plate && (
                      <div>
                        <span className="font-medium">License:</span> {vehicle.license_plate}
                      </div>
                    )}
                    
                    {vehicle.vehicle_type && (
                      <div>
                        <span className="font-medium">Type:</span> {vehicle.vehicle_type}
                      </div>
                    )}
                    
                    <div className="flex items-center gap-1">
                      <Navigation className="w-4 h-4" />
                      <span className="font-medium">Speed:</span> {formatSpeed(vehicle.speed)}
                    </div>
                    
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <span className="font-medium">Updated:</span> {formatTimestamp(vehicle.timestamp)}
                    </div>
                    
                    <div className="mt-3 pt-2 border-t">
                      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        isInside 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {isInside ? 'Inside Geofence' : 'Outside Geofence'}
                      </div>
                    </div>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default Map;

