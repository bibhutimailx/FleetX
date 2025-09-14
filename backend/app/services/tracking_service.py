import asyncio
import logging
from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import SessionLocal, AsyncSessionLocal
from ..models.vehicle import Vehicle, VehicleLocation, GeofenceEvent
from .whilseye_service import whilseye_service
from .geofence_service import geofence_service
from .notification_service import notification_service
from ..core.config import settings

logger = logging.getLogger(__name__)


class TrackingService:
    def __init__(self):
        self.polling_interval = settings.polling_interval
        self.is_running = False
        self.speed_limit = 80.0  # km/h

    async def update_vehicle_locations(self):
        """Fetch and update vehicle locations from WHILSEYE API"""
        try:
            # Get locations from WHILSEYE API
            locations = await whilseye_service.get_all_vehicle_locations()
            
            if not locations:
                logger.warning("No vehicle locations received from WHILSEYE API")
                return

            # Use sync session for database operations
            db = SessionLocal()
            try:
                # Process each location
                for location_data in locations:
                    await self._process_vehicle_location(db, location_data)
                
                # Check for geofence events
                events = await geofence_service.check_geofence_events(db, locations)
                
                # Process geofence events
                for event in events:
                    await self._process_geofence_event(db, event)
                
                # Check for speed alerts
                await self._check_speed_alerts(db, locations)
                
                db.commit()
                logger.info(f"Successfully processed {len(locations)} vehicle locations")
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error processing vehicle locations: {str(e)}")
                raise
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error updating vehicle locations: {str(e)}")

    async def _process_vehicle_location(self, db: Session, location_data: Dict):
        """Process a single vehicle location update"""
        vehicle_id = location_data.get("vehicle_id")
        if not vehicle_id:
            return

        # Ensure vehicle exists
        vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
        if not vehicle:
            vehicle = Vehicle(
                vehicle_id=vehicle_id,
                driver_name=location_data.get("driver_name"),
                license_plate=location_data.get("license_plate"),
                vehicle_type=location_data.get("vehicle_type", "truck")
            )
            db.add(vehicle)
            db.flush()

        # Parse timestamp
        timestamp_str = location_data.get("timestamp")
        try:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = timestamp_str or datetime.utcnow()
        except:
            timestamp = datetime.utcnow()

        # Create location record
        location = VehicleLocation(
            vehicle_id=vehicle_id,
            latitude=location_data.get("latitude"),
            longitude=location_data.get("longitude"),
            speed=location_data.get("speed", 0.0),
            heading=location_data.get("heading", 0.0),
            altitude=location_data.get("altitude", 0.0),
            accuracy=location_data.get("accuracy", 0.0),
            timestamp=timestamp
        )
        
        db.add(location)

    async def _process_geofence_event(self, db: Session, event: GeofenceEvent):
        """Process a geofence event"""
        # Add event to database
        db.add(event)
        db.flush()
        
        # Create activity log
        activity = await geofence_service.create_activity_log(db, event)
        
        # Send notifications
        try:
            notification_result = await notification_service.send_geofence_notification(event)
            
            # Update event with notification status
            event.notification_sent = any(notification_result.values())
            
            logger.info(f"Geofence event processed for vehicle {event.vehicle_id}: {event.event_type}")
            
        except Exception as e:
            logger.error(f"Error sending notifications for geofence event: {str(e)}")

    async def _check_speed_alerts(self, db: Session, locations: List[Dict]):
        """Check for speed limit violations"""
        for location_data in locations:
            speed = location_data.get("speed", 0.0)
            vehicle_id = location_data.get("vehicle_id")
            
            if speed > self.speed_limit and vehicle_id:
                try:
                    await notification_service.send_speed_alert(
                        vehicle_id=vehicle_id,
                        speed=speed,
                        speed_limit=self.speed_limit
                    )
                    logger.info(f"Speed alert sent for vehicle {vehicle_id}: {speed} km/h")
                except Exception as e:
                    logger.error(f"Error sending speed alert: {str(e)}")

    async def start_tracking(self):
        """Start the vehicle tracking service"""
        if self.is_running:
            logger.warning("Tracking service is already running")
            return

        self.is_running = True
        logger.info(f"Starting vehicle tracking service (polling every {self.polling_interval} seconds)")
        
        try:
            while self.is_running:
                await self.update_vehicle_locations()
                await asyncio.sleep(self.polling_interval)
        except asyncio.CancelledError:
            logger.info("Vehicle tracking service cancelled")
        except Exception as e:
            logger.error(f"Error in tracking service: {str(e)}")
        finally:
            self.is_running = False

    def stop_tracking(self):
        """Stop the vehicle tracking service"""
        self.is_running = False
        logger.info("Vehicle tracking service stopped")

    async def get_recent_locations(self, limit: int = 100) -> List[Dict]:
        """Get recent vehicle locations for the frontend"""
        db = SessionLocal()
        try:
            # Get latest location for each vehicle
            subquery = db.query(
                VehicleLocation.vehicle_id,
                VehicleLocation.timestamp.label('max_timestamp')
            ).group_by(VehicleLocation.vehicle_id).subquery()
            
            locations = db.query(VehicleLocation).join(
                subquery,
                (VehicleLocation.vehicle_id == subquery.c.vehicle_id) &
                (VehicleLocation.timestamp == subquery.c.max_timestamp)
            ).limit(limit).all()
            
            # Convert to dict format
            result = []
            for loc in locations:
                vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == loc.vehicle_id).first()
                result.append({
                    "vehicle_id": loc.vehicle_id,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "speed": loc.speed,
                    "heading": loc.heading,
                    "timestamp": loc.timestamp.isoformat(),
                    "driver_name": vehicle.driver_name if vehicle else None,
                    "license_plate": vehicle.license_plate if vehicle else None,
                    "vehicle_type": vehicle.vehicle_type if vehicle else None
                })
            
            return result
            
        finally:
            db.close()


# Create a singleton instance
tracking_service = TrackingService()

