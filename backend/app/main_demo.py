import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from .services.mock_data_service import mock_data_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fleet Management System - Demo",
    description="Real-time vehicle tracking demo with mock data",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass  # Connection might be closed

manager = ConnectionManager()

# Mock database for demo
mock_events = []
mock_activities = []

# API Routes
@app.get("/")
async def root():
    return {
        "message": "Fleet Management System Demo API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/vehicles/")
async def get_vehicles():
    vehicles = mock_data_service.get_vehicles()
    return {
        "vehicles": [
            {
                "id": i + 1,
                "vehicle_id": v["vehicle_id"],
                "driver_name": v["driver_name"],
                "license_plate": v["license_plate"],
                "vehicle_type": v["vehicle_type"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            for i, v in enumerate(vehicles)
        ]
    }

@app.get("/api/v1/vehicles/locations")
async def get_vehicle_locations():
    locations = mock_data_service.get_all_vehicle_locations()
    return {
        "locations": locations,
        "count": len(locations)
    }

@app.get("/api/v1/vehicles/{vehicle_id}/location")
async def get_vehicle_location(vehicle_id: str):
    location = mock_data_service.get_vehicle_location(vehicle_id)
    if not location:
        return {"error": "Vehicle not found"}, 404
    return location

@app.get("/api/v1/vehicles/{vehicle_id}/history")
async def get_vehicle_history(vehicle_id: str, hours: int = 24):
    # Generate mock history data
    history = []
    base_time = datetime.utcnow()
    location = mock_data_service.get_vehicle_location(vehicle_id)
    
    if location:
        for i in range(10):  # Generate 10 history points
            history.append({
                "latitude": location["latitude"] + (i * 0.001),
                "longitude": location["longitude"] + (i * 0.001),
                "speed": location["speed"] + (i * 2),
                "heading": location["heading"],
                "timestamp": (base_time - timedelta(hours=i)).isoformat()
            })
    
    return {
        "vehicle_id": vehicle_id,
        "history": history,
        "count": len(history)
    }

@app.get("/api/v1/vehicles/{vehicle_id}/geofence-status")
async def get_geofence_status(vehicle_id: str):
    location = mock_data_service.get_vehicle_location(vehicle_id)
    if not location:
        return {"error": "Vehicle not found"}, 404
    
    # Mock geofence check (40.7128, -74.0060 with 100m radius)
    geofence_lat, geofence_lng = 40.7128, -74.0060
    vehicle_lat, vehicle_lng = location["latitude"], location["longitude"]
    
    # Simple distance calculation
    distance = ((vehicle_lat - geofence_lat) ** 2 + (vehicle_lng - geofence_lng) ** 2) ** 0.5 * 111000
    is_inside = distance <= 100
    
    return {
        "vehicle_id": vehicle_id,
        "is_inside_geofence": is_inside,
        "distance_to_geofence": distance,
        "geofence_center": {"latitude": geofence_lat, "longitude": geofence_lng},
        "geofence_radius": 100,
        "current_location": {
            "latitude": vehicle_lat,
            "longitude": vehicle_lng,
            "timestamp": location["timestamp"]
        }
    }

@app.get("/api/v1/events/geofence")
async def get_geofence_events(hours: int = 24):
    # Generate some mock events
    events = []
    for i in range(5):
        event = mock_data_service.simulate_geofence_event()
        event["id"] = i + 1
        events.append(event)
    
    return {
        "events": events,
        "count": len(events)
    }

@app.get("/api/v1/events/activity")
async def get_activity_log(hours: int = 24, limit: int = 100):
    activities = []
    vehicles = mock_data_service.get_vehicles()
    
    for i, vehicle in enumerate(vehicles[:3]):  # Create activities for first 3 vehicles
        activities.append({
            "id": i + 1,
            "vehicle_id": vehicle["vehicle_id"],
            "activity_type": "geofence_enter",
            "description": f"Vehicle {vehicle['vehicle_id']} entered Plant Gate",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "metadata": "{}",
            "timestamp": (datetime.utcnow() - timedelta(minutes=i * 30)).isoformat()
        })
    
    return {
        "activities": activities,
        "count": len(activities)
    }

@app.get("/api/v1/events/summary")
async def get_events_summary(hours: int = 24):
    return {
        "summary_period_hours": hours,
        "geofence_events": {
            "enters": 3,
            "exits": 2,
            "total": 5
        },
        "activities_by_type": {
            "geofence_enter": 3,
            "geofence_exit": 2,
            "speed_alert": 1
        },
        "active_vehicles": 5,
        "generated_at": datetime.utcnow().isoformat()
    }

@app.websocket("/ws/vehicle-updates")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial data
        locations = mock_data_service.get_all_vehicle_locations()
        initial_data = {
            "type": "initial_locations",
            "data": locations,
            "timestamp": datetime.utcnow().timestamp()
        }
        await websocket.send_text(json.dumps(initial_data))
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task to broadcast updates
async def broadcast_updates():
    while True:
        if manager.active_connections:
            locations = mock_data_service.get_all_vehicle_locations()
            update_message = {
                "type": "location_update",
                "data": locations,
                "timestamp": datetime.utcnow().timestamp()
            }
            await manager.broadcast(json.dumps(update_message))
        
        await asyncio.sleep(10)  # Update every 10 seconds

@app.on_event("startup")
async def startup_event():
    # Start background task
    asyncio.create_task(broadcast_updates())
    logger.info("Fleet Management Demo API started")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

