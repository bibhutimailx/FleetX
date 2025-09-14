from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from ..core.database import get_db
from ..models.vehicle import GeofenceEvent, ActivityLog

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/geofence")
async def get_geofence_events(
    hours: int = Query(24, description="Number of hours of events to retrieve"),
    vehicle_id: Optional[str] = Query(None, description="Filter by specific vehicle ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type (enter/exit)"),
    db: Session = Depends(get_db)
):
    """Get geofence events"""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    query = db.query(GeofenceEvent).filter(GeofenceEvent.timestamp >= since)
    
    if vehicle_id:
        query = query.filter(GeofenceEvent.vehicle_id == vehicle_id)
    
    if event_type:
        query = query.filter(GeofenceEvent.event_type == event_type)
    
    events = query.order_by(GeofenceEvent.timestamp.desc()).all()
    
    return {
        "events": [
            {
                "id": event.id,
                "vehicle_id": event.vehicle_id,
                "event_type": event.event_type,
                "latitude": event.latitude,
                "longitude": event.longitude,
                "geofence_name": event.geofence_name,
                "timestamp": event.timestamp.isoformat(),
                "notification_sent": event.notification_sent
            }
            for event in events
        ],
        "count": len(events)
    }


@router.get("/activity")
async def get_activity_log(
    hours: int = Query(24, description="Number of hours of activity to retrieve"),
    vehicle_id: Optional[str] = Query(None, description="Filter by specific vehicle ID"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    limit: int = Query(100, description="Maximum number of activities to return"),
    db: Session = Depends(get_db)
):
    """Get activity log"""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    query = db.query(ActivityLog).filter(ActivityLog.timestamp >= since)
    
    if vehicle_id:
        query = query.filter(ActivityLog.vehicle_id == vehicle_id)
    
    if activity_type:
        query = query.filter(ActivityLog.activity_type == activity_type)
    
    activities = query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
    
    return {
        "activities": [
            {
                "id": activity.id,
                "vehicle_id": activity.vehicle_id,
                "activity_type": activity.activity_type,
                "description": activity.description,
                "latitude": activity.latitude,
                "longitude": activity.longitude,
                "metadata": activity.metadata,
                "timestamp": activity.timestamp.isoformat()
            }
            for activity in activities
        ],
        "count": len(activities)
    }


@router.get("/summary")
async def get_events_summary(
    hours: int = Query(24, description="Number of hours to summarize"),
    db: Session = Depends(get_db)
):
    """Get summary of events and activities"""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get geofence event counts
    geofence_enters = db.query(GeofenceEvent).filter(
        GeofenceEvent.timestamp >= since,
        GeofenceEvent.event_type == "enter"
    ).count()
    
    geofence_exits = db.query(GeofenceEvent).filter(
        GeofenceEvent.timestamp >= since,
        GeofenceEvent.event_type == "exit"
    ).count()
    
    # Get activity counts by type
    activities_by_type = db.query(
        ActivityLog.activity_type,
        db.func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.timestamp >= since
    ).group_by(ActivityLog.activity_type).all()
    
    # Get unique vehicles with activity
    active_vehicles = db.query(
        ActivityLog.vehicle_id
    ).filter(
        ActivityLog.timestamp >= since
    ).distinct().count()
    
    return {
        "summary_period_hours": hours,
        "geofence_events": {
            "enters": geofence_enters,
            "exits": geofence_exits,
            "total": geofence_enters + geofence_exits
        },
        "activities_by_type": {
            activity_type: count for activity_type, count in activities_by_type
        },
        "active_vehicles": active_vehicles,
        "generated_at": datetime.utcnow().isoformat()
    }

