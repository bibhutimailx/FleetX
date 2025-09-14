import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fleet Management System - Simple Demo",
    description="Real-time vehicle tracking demo with mock data",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
mock_vehicles = [
    {
        "id": 1,
        "vehicle_id": "TRUCK001",
        "driver_name": "John Smith",
        "license_plate": "NY-1234",
        "vehicle_type": "Heavy Truck",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "speed": 35.5,
        "heading": 180,
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "id": 2,
        "vehicle_id": "TRUCK002", 
        "driver_name": "Sarah Johnson",
        "license_plate": "NY-5678",
        "vehicle_type": "Delivery Van",
        "latitude": 40.7589,
        "longitude": -73.9851,
        "speed": 22.3,
        "heading": 90,
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "id": 3,
        "vehicle_id": "TRUCK003",
        "driver_name": "Mike Wilson",
        "license_plate": "NY-9012", 
        "vehicle_type": "Container Truck",
        "latitude": 40.6892,
        "longitude": -74.0445,
        "speed": 45.2,
        "heading": 270,
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "id": 4,
        "vehicle_id": "TRUCK004",
        "driver_name": "Emma Davis",
        "license_plate": "NY-3456",
        "vehicle_type": "Flatbed Truck",
        "latitude": 40.7831,
        "longitude": -73.9712,
        "speed": 15.8,
        "heading": 45,
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "id": 5,
        "vehicle_id": "TRUCK005",
        "driver_name": "Robert Brown",
        "license_plate": "NY-7890",
        "vehicle_type": "Tanker Truck",
        "latitude": 40.7282,
        "longitude": -73.7949,
        "speed": 60.1,
        "heading": 315,
        "timestamp": datetime.utcnow().isoformat()
    }
]

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

# API Routes
@app.get("/")
async def root():
    return {
        "message": "Fleet Management System Simple Demo API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "demo_endpoints": [
            "/api/v1/vehicles/",
            "/api/v1/vehicles/locations",
            "/api/v1/events/geofence",
            "/api/v1/events/activity"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_connections": len(manager.active_connections),
        "total_vehicles": len(mock_vehicles)
    }

@app.get("/api/v1/vehicles/")
async def get_vehicles():
    return {
        "vehicles": mock_vehicles,
        "count": len(mock_vehicles)
    }

@app.get("/api/v1/vehicles/locations")
async def get_vehicle_locations():
    # Update positions slightly for each request to simulate movement
    import random
    for vehicle in mock_vehicles:
        vehicle["latitude"] += random.uniform(-0.001, 0.001)
        vehicle["longitude"] += random.uniform(-0.001, 0.001)
        vehicle["speed"] = max(0, vehicle["speed"] + random.uniform(-5, 5))
        vehicle["heading"] = (vehicle["heading"] + random.uniform(-10, 10)) % 360
        vehicle["timestamp"] = datetime.utcnow().isoformat()
    
    return {
        "locations": mock_vehicles,
        "count": len(mock_vehicles)
    }

@app.get("/api/v1/vehicles/{vehicle_id}/location")
async def get_vehicle_location(vehicle_id: str):
    for vehicle in mock_vehicles:
        if vehicle["vehicle_id"] == vehicle_id:
            return vehicle
    return {"error": "Vehicle not found"}, 404

@app.get("/api/v1/vehicles/{vehicle_id}/history")
async def get_vehicle_history(vehicle_id: str, hours: int = 24):
    # Find the vehicle
    vehicle = None
    for v in mock_vehicles:
        if v["vehicle_id"] == vehicle_id:
            vehicle = v
            break
    
    if not vehicle:
        return {"error": "Vehicle not found"}, 404
    
    # Generate mock history data
    history = []
    base_time = datetime.utcnow()
    
    for i in range(10):  # Generate 10 history points
        history.append({
            "latitude": vehicle["latitude"] + (i * 0.001),
            "longitude": vehicle["longitude"] + (i * 0.001),
            "speed": max(0, vehicle["speed"] + (i * 2)),
            "heading": vehicle["heading"],
            "timestamp": (base_time - timedelta(hours=i)).isoformat()
        })
    
    return {
        "vehicle_id": vehicle_id,
        "history": history,
        "count": len(history)
    }

@app.get("/api/v1/events/geofence")
async def get_geofence_events(hours: int = 24):
    # Generate some mock geofence events
    import random
    events = []
    for i, vehicle in enumerate(mock_vehicles[:3]):  # Create events for first 3 vehicles
        events.append({
            "id": i + 1,
            "vehicle_id": vehicle["vehicle_id"],
            "event_type": "enter" if i % 2 == 0 else "exit",
            "latitude": 40.7128 + random.uniform(-0.005, 0.005),
            "longitude": -74.0060 + random.uniform(-0.005, 0.005),
            "geofence_name": "Plant Gate",
            "timestamp": (datetime.utcnow() - timedelta(minutes=i * 30)).isoformat(),
            "notification_sent": True
        })
    
    return {
        "events": events,
        "count": len(events)
    }

@app.get("/api/v1/events/activity")
async def get_activity_log(hours: int = 24, limit: int = 100):
    activities = []
    
    for i, vehicle in enumerate(mock_vehicles):
        activities.append({
            "id": i + 1,
            "vehicle_id": vehicle["vehicle_id"],
            "activity_type": "location_update",
            "description": f"Vehicle {vehicle['vehicle_id']} updated location",
            "latitude": vehicle["latitude"],
            "longitude": vehicle["longitude"],
            "metadata": json.dumps({"speed": vehicle["speed"], "heading": vehicle["heading"]}),
            "timestamp": (datetime.utcnow() - timedelta(minutes=i * 15)).isoformat()
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
            "location_update": len(mock_vehicles),
            "geofence_enter": 3,
            "geofence_exit": 2,
            "speed_alert": 1
        },
        "active_vehicles": len(mock_vehicles),
        "generated_at": datetime.utcnow().isoformat()
    }

@app.websocket("/ws/vehicle-updates")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial data
        initial_data = {
            "type": "initial_locations",
            "data": mock_vehicles,
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
    import random
    while True:
        if manager.active_connections:
            # Update vehicle positions
            for vehicle in mock_vehicles:
                vehicle["latitude"] += random.uniform(-0.0005, 0.0005)
                vehicle["longitude"] += random.uniform(-0.0005, 0.0005)
                vehicle["speed"] = max(0, vehicle["speed"] + random.uniform(-2, 2))
                vehicle["heading"] = (vehicle["heading"] + random.uniform(-5, 5)) % 360
                vehicle["timestamp"] = datetime.utcnow().isoformat()
            
            update_message = {
                "type": "location_update",
                "data": mock_vehicles,
                "timestamp": datetime.utcnow().timestamp()
            }
            await manager.broadcast(json.dumps(update_message))
        
        await asyncio.sleep(5)  # Update every 5 seconds

# Background task to broadcast updates
async def broadcast_updates():
    import random
    while True:
        if manager.active_connections:
            # Update vehicle positions
            for vehicle in mock_vehicles:
                vehicle["latitude"] += random.uniform(-0.0005, 0.0005)
                vehicle["longitude"] += random.uniform(-0.0005, 0.0005)
                vehicle["speed"] = max(0, vehicle["speed"] + random.uniform(-2, 2))
                vehicle["heading"] = (vehicle["heading"] + random.uniform(-5, 5)) % 360
                vehicle["timestamp"] = datetime.utcnow().isoformat()
            
            update_message = {
                "type": "location_update",
                "data": mock_vehicles,
                "timestamp": datetime.utcnow().timestamp()
            }
            await manager.broadcast(json.dumps(update_message))
        
        await asyncio.sleep(5)  # Update every 5 seconds

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(broadcast_updates())
    logger.info("Fleet Management Simple Demo API started")
    logger.info("Available endpoints:")
    logger.info("  GET /")
    logger.info("  GET /health")
    logger.info("  GET /docs (API documentation)")
    logger.info("  GET /api/v1/vehicles/")
    logger.info("  GET /api/v1/vehicles/locations")
    logger.info("  WS /ws/vehicle-updates")
    yield
    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
