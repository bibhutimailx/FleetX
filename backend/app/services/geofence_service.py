import math
from typing import Dict, List, Optional
from datetime import datetime
from geopy.distance import geodesic
from sqlalchemy.orm import Session
from ..models.vehicle import VehicleLocation, GeofenceEvent, ActivityLog
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


class GeofenceService:
    def __init__(self):
        self.plant_gate_lat = settings.geofence_lat
        self.plant_gate_lng = settings.geofence_lng
        self.geofence_radius = settings.geofence_radius  # meters

    def is_inside_geofence(self, latitude: float, longitude: float) -> bool:
        """Check if a location is inside the plant gate geofence"""
        try:
            plant_gate = (self.plant_gate_lat, self.plant_gate_lng)
            vehicle_location = (latitude, longitude)
            
            distance = geodesic(plant_gate, vehicle_location).meters
            return distance <= self.geofence_radius
        except Exception as e:
            logger.error(f"Error checking geofence: {str(e)}")
            return False

    def get_distance_to_geofence(self, latitude: float, longitude: float) -> float:
        """Get distance in meters to the plant gate geofence center"""
        try:
            plant_gate = (self.plant_gate_lat, self.plant_gate_lng)
            vehicle_location = (latitude, longitude)
            return geodesic(plant_gate, vehicle_location).meters
        except Exception as e:
            logger.error(f"Error calculating distance: {str(e)}")
            return float('inf')

    async def check_geofence_events(self, db: Session, vehicle_locations: List[Dict]) -> List[GeofenceEvent]:
        """Check for geofence entry/exit events"""
        events = []
        
        for location_data in vehicle_locations:
            vehicle_id = location_data.get("vehicle_id")
            if not vehicle_id:
                continue
                
            latitude = location_data.get("latitude")
            longitude = location_data.get("longitude")
            timestamp_str = location_data.get("timestamp")
            
            if not all([latitude, longitude, timestamp_str]):
                continue
                
            try:
                if isinstance(timestamp_str, str):
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = timestamp_str
            except:
                timestamp = datetime.utcnow()

            # Check if vehicle is currently inside geofence
            is_inside = self.is_inside_geofence(latitude, longitude)
            
            # Get the last known location for this vehicle
            last_location = db.query(VehicleLocation).filter(
                VehicleLocation.vehicle_id == vehicle_id
            ).order_by(VehicleLocation.timestamp.desc()).first()
            
            if last_location:
                was_inside = self.is_inside_geofence(last_location.latitude, last_location.longitude)
                
                # Check for entry event
                if not was_inside and is_inside:
                    event = GeofenceEvent(
                        vehicle_id=vehicle_id,
                        event_type="enter",
                        latitude=latitude,
                        longitude=longitude,
                        geofence_name="Plant Gate",
                        timestamp=timestamp
                    )
                    events.append(event)
                    logger.info(f"Vehicle {vehicle_id} entered geofence")
                
                # Check for exit event
                elif was_inside and not is_inside:
                    event = GeofenceEvent(
                        vehicle_id=vehicle_id,
                        event_type="exit",
                        latitude=latitude,
                        longitude=longitude,
                        geofence_name="Plant Gate",
                        timestamp=timestamp
                    )
                    events.append(event)
                    logger.info(f"Vehicle {vehicle_id} exited geofence")
            
            elif is_inside:
                # First time seeing this vehicle and it's inside
                event = GeofenceEvent(
                    vehicle_id=vehicle_id,
                    event_type="enter",
                    latitude=latitude,
                    longitude=longitude,
                    geofence_name="Plant Gate",
                    timestamp=timestamp
                )
                events.append(event)
                logger.info(f"Vehicle {vehicle_id} initially detected inside geofence")
        
        return events

    async def create_activity_log(self, db: Session, event: GeofenceEvent) -> ActivityLog:
        """Create an activity log entry for a geofence event"""
        description = f"Vehicle {event.vehicle_id} {'entered' if event.event_type == 'enter' else 'exited'} {event.geofence_name}"
        
        activity = ActivityLog(
            vehicle_id=event.vehicle_id,
            activity_type=f"geofence_{event.event_type}",
            description=description,
            latitude=event.latitude,
            longitude=event.longitude,
            timestamp=event.timestamp
        )
        
        db.add(activity)
        return activity


# Create a singleton instance
geofence_service = GeofenceService()

