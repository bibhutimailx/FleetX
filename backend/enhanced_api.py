import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import random
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enhanced Fleet Management System",
    description="Fleet management with route tracking, deviation detection, and alerts",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class RoutePoint(BaseModel):
    latitude: float
    longitude: float
    name: str
    type: str  # "plant_stockyard", "destination", "waypoint"

class VehicleStatus(BaseModel):
    vehicle_id: str
    driver_name: str
    license_plate: str
    vehicle_type: str
    latitude: float
    longitude: float
    speed: float
    heading: float
    timestamp: str
    material_loaded: bool
    load_status: str  # "empty", "loading", "loaded", "unloading"
    route_status: str  # "on_route", "deviation", "stopped"
    stop_duration: int  # minutes
    last_movement: str
    destination_eta: Optional[str]

class Alert(BaseModel):
    id: str
    vehicle_id: str
    alert_type: str  # "route_deviation", "extended_stop", "speed_violation"
    message: str
    severity: str  # "low", "medium", "high"
    timestamp: str
    status: str  # "active", "acknowledged", "resolved"

# Route Configuration
PLANT_STOCKYARD = {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "name": "Plant Stockyard",
    "radius": 100  # meters
}

DESTINATION = {
    "latitude": 40.7831,
    "longitude": -73.9712,
    "name": "Destination Site",
    "radius": 150  # meters
}

# Predefined route waypoints (simplified Google Maps route)
ROUTE_WAYPOINTS = [
    {"latitude": 40.7128, "longitude": -74.0060, "name": "Plant Stockyard"},
    {"latitude": 40.7200, "longitude": -73.9950, "name": "Waypoint 1"},
    {"latitude": 40.7350, "longitude": -73.9850, "name": "Waypoint 2"},
    {"latitude": 40.7500, "longitude": -73.9750, "name": "Waypoint 3"},
    {"latitude": 40.7650, "longitude": -73.9700, "name": "Waypoint 4"},
    {"latitude": 40.7831, "longitude": -73.9712, "name": "Destination Site"}
]

# Mock data with enhanced tracking
mock_vehicles = [
    {
        "id": 1,
        "vehicle_id": "TRUCK001",
        "driver_name": "John Smith",
        "license_plate": "NY-1234",
        "vehicle_type": "Heavy Truck",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "speed": 0,
        "heading": 90,
        "timestamp": datetime.utcnow().isoformat(),
        "material_loaded": True,
        "load_status": "loaded",
        "route_status": "on_route",
        "stop_duration": 0,
        "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-13T12:30:00",
        "route_progress": 0  # 0-100%
    },
    {
        "id": 2,
        "vehicle_id": "TRUCK002", 
        "driver_name": "Sarah Johnson",
        "license_plate": "NY-5678",
        "vehicle_type": "Delivery Van",
        "latitude": 40.7350,
        "longitude": -73.9850,
        "speed": 45,
        "heading": 85,
        "timestamp": datetime.utcnow().isoformat(),
        "material_loaded": True,
        "load_status": "loaded",
        "route_status": "on_route",
        "stop_duration": 0,
        "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-13T12:15:00",
        "route_progress": 45
    },
    {
        "id": 3,
        "vehicle_id": "TRUCK003",
        "driver_name": "Mike Wilson",
        "license_plate": "NY-9012", 
        "vehicle_type": "Container Truck",
        "latitude": 40.7200,
        "longitude": -73.9950,
        "speed": 0,
        "heading": 90,
        "timestamp": datetime.utcnow().isoformat(),
        "material_loaded": True,
        "load_status": "loaded",
        "route_status": "stopped",
        "stop_duration": 35,  # Violation: stopped for 35 minutes
        "last_movement": (datetime.utcnow() - timedelta(minutes=35)).isoformat(),
        "destination_eta": "2025-09-13T13:00:00",
        "route_progress": 25
    }
]

# Alert storage
active_alerts = []

# Utility Functions
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters"""
    R = 6371000  # Earth's radius in meters
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon/2) * math.sin(delta_lon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def is_on_route(vehicle_lat, vehicle_lon, max_deviation=200):
    """Check if vehicle is within acceptable distance from route"""
    for waypoint in ROUTE_WAYPOINTS:
        distance = calculate_distance(
            vehicle_lat, vehicle_lon,
            waypoint["latitude"], waypoint["longitude"]
        )
        if distance <= max_deviation:
            return True
    return False

def check_for_alerts(vehicle):
    """Check vehicle for various alert conditions"""
    alerts = []
    
    # Check for extended stops (>30 minutes)
    if vehicle["speed"] == 0 and vehicle["stop_duration"] > 30:
        alerts.append({
            "id": f"stop_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
            "vehicle_id": vehicle["vehicle_id"],
            "alert_type": "extended_stop",
            "message": f"Vehicle {vehicle['vehicle_id']} has been stopped for {vehicle['stop_duration']} minutes",
            "severity": "high",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active"
        })
    
    # Check for route deviation
    if not is_on_route(vehicle["latitude"], vehicle["longitude"]):
        alerts.append({
            "id": f"deviation_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
            "vehicle_id": vehicle["vehicle_id"],
            "alert_type": "route_deviation",
            "message": f"Vehicle {vehicle['vehicle_id']} has deviated from the predefined route",
            "severity": "high",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active"
        })
    
    # Check for speed violations (>80 km/h)
    if vehicle["speed"] > 80:
        alerts.append({
            "id": f"speed_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
            "vehicle_id": vehicle["vehicle_id"],
            "alert_type": "speed_violation",
            "message": f"Vehicle {vehicle['vehicle_id']} exceeding speed limit: {vehicle['speed']:.1f} km/h",
            "severity": "medium",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active"
        })
    
    return alerts

def simulate_vehicle_movement(vehicle):
    """Simulate realistic vehicle movement along route"""
    # Simulate movement for vehicles that are "on_route"
    if vehicle["route_status"] == "on_route" and vehicle["speed"] > 0:
        # Move vehicle slightly along route
        progress = vehicle["route_progress"]
        if progress < 100:
            # Simple linear interpolation between waypoints
            progress += random.uniform(0.5, 2.0)  # Progress 0.5-2% per update
            vehicle["route_progress"] = min(progress, 100)
            
            # Calculate position based on progress
            waypoint_index = int(progress / 20)  # 5 waypoints, 20% each
            if waypoint_index < len(ROUTE_WAYPOINTS) - 1:
                start_point = ROUTE_WAYPOINTS[waypoint_index]
                end_point = ROUTE_WAYPOINTS[waypoint_index + 1]
                
                # Interpolate position
                local_progress = (progress % 20) / 20
                vehicle["latitude"] = (start_point["latitude"] + 
                                    (end_point["latitude"] - start_point["latitude"]) * local_progress)
                vehicle["longitude"] = (start_point["longitude"] + 
                                      (end_point["longitude"] - start_point["longitude"]) * local_progress)
    
    # Add some random variation
    if vehicle["speed"] > 0:
        vehicle["latitude"] += random.uniform(-0.0002, 0.0002)
        vehicle["longitude"] += random.uniform(-0.0002, 0.0002)
        vehicle["speed"] = max(0, vehicle["speed"] + random.uniform(-5, 5))
    
    # Update stop duration
    if vehicle["speed"] == 0:
        last_movement = datetime.fromisoformat(vehicle["last_movement"].replace('Z', '+00:00'))
        vehicle["stop_duration"] = int((datetime.utcnow() - last_movement.replace(tzinfo=None)).total_seconds() / 60)
    else:
        vehicle["last_movement"] = datetime.utcnow().isoformat()
        vehicle["stop_duration"] = 0
    
    vehicle["timestamp"] = datetime.utcnow().isoformat()

# API Routes
@app.get("/")
async def root():
    return {
        "message": "Enhanced Fleet Management System",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/docs",
        "features": [
            "Route tracking",
            "Deviation detection", 
            "Stop time monitoring",
            "Material loading status",
            "Alert system"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "total_vehicles": len(mock_vehicles),
        "active_alerts": len([a for a in active_alerts if a["status"] == "active"])
    }

@app.get("/api/v1/vehicles/")
async def get_vehicles():
    return {
        "vehicles": mock_vehicles,
        "count": len(mock_vehicles)
    }

@app.get("/api/v1/vehicles/locations")
async def get_vehicle_locations():
    # Update vehicle positions and check for alerts
    global active_alerts
    
    for vehicle in mock_vehicles:
        simulate_vehicle_movement(vehicle)
        
        # Check for new alerts
        new_alerts = check_for_alerts(vehicle)
        for alert in new_alerts:
            # Avoid duplicate alerts
            existing = [a for a in active_alerts if 
                       a["vehicle_id"] == alert["vehicle_id"] and 
                       a["alert_type"] == alert["alert_type"] and 
                       a["status"] == "active"]
            if not existing:
                active_alerts.append(alert)
                logger.warning(f"Alert generated: {alert['message']}")
    
    return {
        "locations": mock_vehicles,
        "count": len(mock_vehicles)
    }

@app.get("/api/v1/route/")
async def get_route_info():
    return {
        "plant_stockyard": PLANT_STOCKYARD,
        "destination": DESTINATION,
        "waypoints": ROUTE_WAYPOINTS,
        "total_distance_km": 15.2,
        "estimated_time_minutes": 45
    }

@app.get("/api/v1/alerts/")
async def get_alerts(status: str = "active"):
    filtered_alerts = [a for a in active_alerts if a["status"] == status]
    return {
        "alerts": filtered_alerts,
        "count": len(filtered_alerts)
    }

@app.post("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    for alert in active_alerts:
        if alert["id"] == alert_id:
            alert["status"] = "acknowledged"
            alert["acknowledged_at"] = datetime.utcnow().isoformat()
            return {"message": "Alert acknowledged", "alert": alert}
    return {"error": "Alert not found"}, 404

@app.get("/api/v1/vehicles/{vehicle_id}/status")
async def get_vehicle_status(vehicle_id: str):
    vehicle = next((v for v in mock_vehicles if v["vehicle_id"] == vehicle_id), None)
    if not vehicle:
        return {"error": "Vehicle not found"}, 404
    
    # Calculate additional status info
    distance_to_destination = calculate_distance(
        vehicle["latitude"], vehicle["longitude"],
        DESTINATION["latitude"], DESTINATION["longitude"]
    )
    
    return {
        **vehicle,
        "distance_to_destination_m": distance_to_destination,
        "is_on_route": is_on_route(vehicle["latitude"], vehicle["longitude"]),
        "alerts": [a for a in active_alerts if a["vehicle_id"] == vehicle_id and a["status"] == "active"]
    }

@app.post("/api/v1/vehicles/{vehicle_id}/load-material")
async def load_material(vehicle_id: str):
    vehicle = next((v for v in mock_vehicles if v["vehicle_id"] == vehicle_id), None)
    if not vehicle:
        return {"error": "Vehicle not found"}, 404
    
    vehicle["material_loaded"] = True
    vehicle["load_status"] = "loaded"
    vehicle["timestamp"] = datetime.utcnow().isoformat()
    
    return {
        "message": f"Material loaded for vehicle {vehicle_id}",
        "vehicle": vehicle
    }

@app.get("/api/v1/analytics/summary")
async def get_analytics_summary():
    total_vehicles = len(mock_vehicles)
    on_route = len([v for v in mock_vehicles if v["route_status"] == "on_route"])
    stopped = len([v for v in mock_vehicles if v["route_status"] == "stopped"])
    loaded_vehicles = len([v for v in mock_vehicles if v["material_loaded"]])
    
    return {
        "total_vehicles": total_vehicles,
        "on_route": on_route,
        "stopped": stopped,
        "deviations": len([v for v in mock_vehicles if v["route_status"] == "deviation"]),
        "loaded_vehicles": loaded_vehicles,
        "active_alerts": len([a for a in active_alerts if a["status"] == "active"]),
        "average_progress": sum([v["route_progress"] for v in mock_vehicles]) / total_vehicles if total_vehicles > 0 else 0,
        "generated_at": datetime.utcnow().isoformat()
    }

# Notification system (mock)
async def send_notification(alert):
    """Mock notification system for SMS/Email alerts"""
    logger.info(f"🚨 ALERT NOTIFICATION:")
    logger.info(f"   Type: {alert['alert_type']}")
    logger.info(f"   Vehicle: {alert['vehicle_id']}")
    logger.info(f"   Message: {alert['message']}")
    logger.info(f"   📧 Email sent to fleet manager")
    logger.info(f"   📱 SMS sent to driver and supervisor")

# Background monitoring task
async def monitor_fleet():
    """Background task to continuously monitor fleet and generate alerts"""
    while True:
        try:
            # This would normally check real GPS data
            for vehicle in mock_vehicles:
                alerts = check_for_alerts(vehicle)
                for alert in alerts:
                    # Check if this is a new alert
                    existing = [a for a in active_alerts if 
                              a["vehicle_id"] == alert["vehicle_id"] and 
                              a["alert_type"] == alert["alert_type"] and 
                              a["status"] == "active"]
                    if not existing:
                        active_alerts.append(alert)
                        await send_notification(alert)
            
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Error in fleet monitoring: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_fleet())
    logger.info("Enhanced Fleet Management System started")
    logger.info("Features: Route tracking, Deviation detection, Stop monitoring, Alerts")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003, reload=True)
