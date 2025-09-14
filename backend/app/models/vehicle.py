from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from ..core.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, unique=True, index=True, nullable=False)
    driver_name = Column(String)
    license_plate = Column(String)
    vehicle_type = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)


class VehicleLocation(Base):
    __tablename__ = "vehicle_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, default=0.0)
    heading = Column(Float, default=0.0)
    altitude = Column(Float, default=0.0)
    accuracy = Column(Float, default=0.0)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GeofenceEvent(Base):
    __tablename__ = "geofence_events"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, index=True, nullable=False)
    event_type = Column(String, nullable=False)  # 'enter' or 'exit'
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geofence_name = Column(String, default="Plant Gate")
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notification_sent = Column(Boolean, default=False)


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, index=True, nullable=False)
    activity_type = Column(String, nullable=False)  # 'geofence_enter', 'geofence_exit', 'speed_alert', etc.
    description = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    metadata = Column(Text)  # JSON string for additional data
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

