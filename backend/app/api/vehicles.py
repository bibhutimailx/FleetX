from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from ..core.database import get_db
from ..models.vehicle import Vehicle, VehicleLocation, GeofenceEvent, ActivityLog
from ..services.tracking_service import tracking_service
from ..services.geofence_service import geofence_service

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/")
async def get_vehicles(db: Session = Depends(get_db)):
    """Get all vehicles"""
    vehicles = db.query(Vehicle).filter(Vehicle.is_active == True).all()
    return {
        "vehicles": [
            {
                "id": v.id,
                "vehicle_id": v.vehicle_id,
                "driver_name": v.driver_name,
                "license_plate": v.license_plate,
                "vehicle_type": v.vehicle_type,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "updated_at": v.updated_at.isoformat() if v.updated_at else None
            }
            for v in vehicles
        ]
    }


@router.get("/locations")
async def get_vehicle_locations(
    limit: int = Query(100, description="Maximum number of locations to return"),
    vehicle_id: Optional[str] = Query(None, description="Filter by specific vehicle ID")
):
    """Get recent vehicle locations"""
    try:
        locations = await tracking_service.get_recent_locations(limit=limit)
        
        if vehicle_id:
            locations = [loc for loc in locations if loc["vehicle_id"] == vehicle_id]
        
        return {
            "locations": locations,
            "count": len(locations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vehicle_id}/location")
async def get_vehicle_current_location(vehicle_id: str, db: Session = Depends(get_db)):
    """Get current location of a specific vehicle"""
    location = db.query(VehicleLocation).filter(
        VehicleLocation.vehicle_id == vehicle_id
    ).order_by(VehicleLocation.timestamp.desc()).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Vehicle location not found")
    
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    
    return {
        "vehicle_id": location.vehicle_id,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "speed": location.speed,
        "heading": location.heading,
        "altitude": location.altitude,
        "accuracy": location.accuracy,
        "timestamp": location.timestamp.isoformat(),
        "driver_name": vehicle.driver_name if vehicle else None,
        "license_plate": vehicle.license_plate if vehicle else None,
        "vehicle_type": vehicle.vehicle_type if vehicle else None
    }


@router.get("/{vehicle_id}/history")
async def get_vehicle_location_history(
    vehicle_id: str,
    hours: int = Query(24, description="Number of hours of history to retrieve"),
    db: Session = Depends(get_db)
):
    """Get location history for a specific vehicle"""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    locations = db.query(VehicleLocation).filter(
        VehicleLocation.vehicle_id == vehicle_id,
        VehicleLocation.timestamp >= since
    ).order_by(VehicleLocation.timestamp.desc()).all()
    
    return {
        "vehicle_id": vehicle_id,
        "history": [
            {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "speed": loc.speed,
                "heading": loc.heading,
                "timestamp": loc.timestamp.isoformat()
            }
            for loc in locations
        ],
        "count": len(locations)
    }


@router.get("/{vehicle_id}/geofence-status")
async def get_vehicle_geofence_status(vehicle_id: str, db: Session = Depends(get_db)):
    """Check if vehicle is currently inside geofence"""
    location = db.query(VehicleLocation).filter(
        VehicleLocation.vehicle_id == vehicle_id
    ).order_by(VehicleLocation.timestamp.desc()).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Vehicle location not found")
    
    is_inside = geofence_service.is_inside_geofence(location.latitude, location.longitude)
    distance = geofence_service.get_distance_to_geofence(location.latitude, location.longitude)
    
    return {
        "vehicle_id": vehicle_id,
        "is_inside_geofence": is_inside,
        "distance_to_geofence": distance,
        "geofence_center": {
            "latitude": geofence_service.plant_gate_lat,
            "longitude": geofence_service.plant_gate_lng
        },
        "geofence_radius": geofence_service.geofence_radius,
        "current_location": {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timestamp": location.timestamp.isoformat()
        }
    }

