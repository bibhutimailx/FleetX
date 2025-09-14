import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fleet Management System - Simple API",
    description="Real-time vehicle tracking with mock data",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    }
]

# API Routes
@app.get("/")
async def root():
    return {
        "message": "Fleet Management System API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "total_vehicles": len(mock_vehicles)
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
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
    # Update positions slightly to simulate movement
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)
