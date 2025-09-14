import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import random
import math
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NTPC Fleet Management System - Critical Operations",
    description="Advanced fleet management with critical incident paging and smart gate camera integration",
    version="4.0.0"
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
class CriticalIncident(BaseModel):
    id: str
    vehicle_id: str
    incident_type: str
    severity: str
    message: str
    location: dict
    timestamp: str
    acknowledged: bool
    paged_contacts: List[str]

class GateEntry(BaseModel):
    id: str
    vehicle_id: str
    number_plate: str
    driver_name: str
    entry_time: str
    exit_time: Optional[str]
    camera_image: Optional[str]
    gate_officer: str
    load_weight: Optional[float]

# Enhanced Route Configuration
PLANT_STOCKYARD = {
    "latitude": 20.9463,
    "longitude": 85.2190,
    "name": "NTPC Talcher Super Thermal Power Station",
    "address": "Talcher, Angul, Odisha, India",
    "radius": 200,
    "smart_cameras": [
        {"id": "CAM_GATE_01", "location": "Main Entry Gate", "active": True},
        {"id": "CAM_GATE_02", "location": "Secondary Gate", "active": True},
        {"id": "CAM_LOAD_01", "location": "Loading Bay A", "active": True},
        {"id": "CAM_LOAD_02", "location": "Loading Bay B", "active": True}
    ]
}

DESTINATION = {
    "latitude": 20.8739,
    "longitude": 86.0891,
    "name": "Chandilkhol Industrial Area",
    "address": "Chandilkhol, Jajpur, Odisha, India", 
    "radius": 200
}

# Critical contact list for incident paging
CRITICAL_CONTACTS = [
    {
        "name": "Fleet Manager", 
        "phone": "+91-9437100001", 
        "email": "fleet.manager@ntpc.co.in", 
        "role": "manager",
        "priority": 1,
        "pager": "+91-9437200001"
    },
    {
        "name": "IT Emergency Team", 
        "phone": "+91-9437100002", 
        "email": "it.emergency@ntpc.co.in", 
        "role": "it",
        "priority": 1,
        "pager": "+91-9437200002"
    },
    {
        "name": "Operations Control Room", 
        "phone": "+91-9437100003", 
        "email": "operations.control@ntpc.co.in", 
        "role": "operations",
        "priority": 1,
        "pager": "+91-9437200003"
    },
    {
        "name": "Safety Emergency Team", 
        "phone": "+91-9437100004", 
        "email": "safety.emergency@ntpc.co.in", 
        "role": "safety",
        "priority": 1,
        "pager": "+91-9437200004"
    },
    {
        "name": "Plant Security Chief", 
        "phone": "+91-9437100005", 
        "email": "security.chief@ntpc.co.in", 
        "role": "security",
        "priority": 2,
        "pager": "+91-9437200005"
    },
    {
        "name": "Transport Supervisor", 
        "phone": "+91-9437100006", 
        "email": "transport.supervisor@ntpc.co.in", 
        "role": "transport",
        "priority": 2,
        "pager": "+91-9437200006"
    }
]

# Enhanced mock vehicles with gate tracking
mock_vehicles = [
    {
        "id": 1, "vehicle_id": "OD-03-NT-1001", "driver_name": "Rajesh Kumar", "driver_phone": "+91-9437123001",
        "license_plate": "OD-03-NT-1001", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9463, "longitude": 85.2190, "speed": 0, "heading": 90,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-13T15:30:00", "route_progress": 5, "fuel_level": 85,
        "gate_entry_logged": True, "last_gate_scan": datetime.utcnow().isoformat()
    },
    {
        "id": 2, "vehicle_id": "OD-03-NT-1002", "driver_name": "Santosh Patel", "driver_phone": "+91-9437123002",
        "license_plate": "OD-03-NT-1002", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9680, "longitude": 85.2890, "speed": 45, "heading": 85,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-13T15:15:00", "route_progress": 25, "fuel_level": 78,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(minutes=30)).isoformat()
    },
    {
        "id": 3, "vehicle_id": "OD-03-NT-1003", "driver_name": "Manoj Behera", "driver_phone": "+91-9437123003",
        "license_plate": "OD-03-NT-1003", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9950, "longitude": 85.4200, "speed": 0, "heading": 90,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "critical_stop", "stop_duration": 65, "last_movement": (datetime.utcnow() - timedelta(minutes=65)).isoformat(),
        "destination_eta": "2025-09-13T16:00:00", "route_progress": 45, "fuel_level": 65,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=1)).isoformat()
    },
    # Add more vehicles...
    {
        "id": 4, "vehicle_id": "OD-03-NT-1004", "driver_name": "Sushant Jena", "driver_phone": "+91-9437123004",
        "license_plate": "OD-03-NT-1004", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 21.0500, "longitude": 85.5500, "speed": 95, "heading": 80,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "critical_speed", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-13T14:45:00", "route_progress": 55, "fuel_level": 72,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=1, minutes=15)).isoformat()
    }
]

# Storage for incidents and gate entries
critical_incidents = []
gate_entries = []

# Mock gate entry data
gate_entries = [
    {
        "id": "GATE_001",
        "vehicle_id": "OD-03-NT-1001",
        "number_plate": "OD-03-NT-1001",
        "driver_name": "Rajesh Kumar",
        "entry_time": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "exit_time": None,
        "camera_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD//gA7Q1JFQVRPUjogZ2QtanBlZyB2MS4wICh1c2luZyBJSkcgSlBFRyB2NjIpLCBxdWFsaXR5ID0gODAK/9sAQwAIBgYHBgUIBwcHCQkICgwUDQwLCwwZEhMPFB0aHx4dGhwcICQuJyAiLCMcHCg3KSwwMTQ0NB8nOT04MjwuMzQy/9sAQwEJCQkMCwwYDQ0YMiEcITIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIy/8AAEQgAUABQAwEiAAIRAQMRAf/EAB8AAAEFAQEBAQEBAAAAAAAAAAABAgMEBQYHCAkKC//EALUQAAIBAwMCBAMFBQQEAAABfQECAwAEEQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiUpLTExNTk9QUVJTU",
        "gate_officer": "Security Officer Raman Das",
        "load_weight": 24.5
    },
    {
        "id": "GATE_002",
        "vehicle_id": "OD-03-NT-1002",
        "number_plate": "OD-03-NT-1002",
        "driver_name": "Santosh Patel",
        "entry_time": (datetime.utcnow() - timedelta(hours=1, minutes=30)).isoformat(),
        "exit_time": None,
        "camera_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD//gA7Q1JFQVRPUjogZ2QtanBlZyB2MS4wICh1c2luZyBJSkcgSlBFRyB2NjIpLCBxdWFsaXR5ID0gODAK/9sAQwAIBgYHBgUIBwcHCQkICgwUDQwLCwwZEhMPFB0aHx4dGhwcICQuJyAiLCMcHCg3KSwwMTQ0NB8nOT04MjwuMzQy/9sAQwEJCQkMCwwYDQ0YMiEcITIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIy/8AAEQgAUABQAwEiAAIRAQMRAf/EAB8AAAEFAQEBAQEBAAAAAAAAAAABAgMEBQYHCAkKC//EALUQAAIBAwMCBAMFBQQEAAABfQECAwAEERUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiUpLTExNTk9QUVJTU",
        "gate_officer": "Security Officer Prakash Singh",
        "load_weight": 25.2
    }
]

# Enhanced utility functions
def trigger_critical_incident_paging(incident):
    """Trigger immediate paging for critical incidents"""
    paged_contacts = []
    
    # Determine which contacts to page based on incident type
    priority_contacts = [c for c in CRITICAL_CONTACTS if c["priority"] == 1]
    
    for contact in priority_contacts:
        # Mock paging system - in production integrate with SMS/Pager APIs
        logger.critical(f"🚨 CRITICAL INCIDENT PAGING:")
        logger.critical(f"   📟 PAGER: {contact['pager']}")
        logger.critical(f"   📱 SMS: {contact['phone']}")
        logger.critical(f"   📧 EMAIL: {contact['email']}")
        logger.critical(f"   👤 CONTACT: {contact['name']} ({contact['role'].upper()})")
        logger.critical(f"   🚛 VEHICLE: {incident['vehicle_id']}")
        logger.critical(f"   ⚠️  INCIDENT: {incident['incident_type'].upper()}")
        logger.critical(f"   📍 LOCATION: {incident.get('location', {}).get('description', 'Unknown')}")
        logger.critical(f"   💬 MESSAGE: {incident['message']}")
        logger.critical(f"   ⏰ TIME: {incident['timestamp']}")
        logger.critical(f"   🔴 SEVERITY: {incident['severity'].upper()}")
        
        paged_contacts.append(contact['name'])
    
    return paged_contacts

def simulate_smart_camera_scan(vehicle_id):
    """Simulate smart camera scanning vehicle number plate"""
    # Mock camera detection with confidence score
    camera_data = {
        "camera_id": "CAM_GATE_01",
        "scan_time": datetime.utcnow().isoformat(),
        "number_plate_detected": vehicle_id,
        "confidence_score": random.uniform(0.85, 0.99),
        "image_quality": "HIGH" if random.random() > 0.2 else "MEDIUM",
        "detection_method": "OCR + AI",
        "camera_location": "Main Entry Gate - NTPC Talcher"
    }
    
    logger.info(f"📷 SMART CAMERA SCAN:")
    logger.info(f"   🎯 Vehicle Detected: {vehicle_id}")
    logger.info(f"   📊 Confidence: {camera_data['confidence_score']:.2%}")
    logger.info(f"   📸 Quality: {camera_data['image_quality']}")
    logger.info(f"   📍 Location: {camera_data['camera_location']}")
    
    return camera_data

def check_critical_incidents(vehicle):
    """Enhanced incident detection with critical paging"""
    incidents = []
    
    # Critical stop incident (>60 minutes)
    if vehicle["speed"] == 0 and vehicle["stop_duration"] > 60:
        incident = {
            "id": f"CRITICAL_STOP_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
            "vehicle_id": vehicle["vehicle_id"],
            "incident_type": "critical_extended_stop",
            "severity": "critical",
            "message": f"CRITICAL: Vehicle {vehicle['vehicle_id']} stopped for {vehicle['stop_duration']} minutes - Driver: {vehicle['driver_name']} ({vehicle['driver_phone']})",
            "location": {
                "lat": vehicle["latitude"],
                "lng": vehicle["longitude"],
                "description": get_nearest_landmark(vehicle["latitude"], vehicle["longitude"])
            },
            "timestamp": datetime.utcnow().isoformat(),
            "acknowledged": False,
            "requires_paging": True
        }
        incidents.append(incident)
    
    # Critical speed violation (>90 km/h)
    if vehicle["speed"] > 90:
        incident = {
            "id": f"CRITICAL_SPEED_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
            "vehicle_id": vehicle["vehicle_id"],
            "incident_type": "critical_speed_violation",
            "severity": "critical",
            "message": f"CRITICAL: Vehicle {vehicle['vehicle_id']} exceeding 90 km/h (Current: {vehicle['speed']:.1f} km/h) - Driver: {vehicle['driver_name']} ({vehicle['driver_phone']})",
            "location": {
                "lat": vehicle["latitude"],
                "lng": vehicle["longitude"],
                "description": get_nearest_landmark(vehicle["latitude"], vehicle["longitude"])
            },
            "timestamp": datetime.utcnow().isoformat(),
            "acknowledged": False,
            "requires_paging": True
        }
        incidents.append(incident)
    
    # Route deviation for extended period (>30 minutes)
    if not is_on_route(vehicle["latitude"], vehicle["longitude"])[0] and vehicle["stop_duration"] > 30:
        incident = {
            "id": f"CRITICAL_DEVIATION_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
            "vehicle_id": vehicle["vehicle_id"],
            "incident_type": "critical_route_deviation",
            "severity": "critical",
            "message": f"CRITICAL: Vehicle {vehicle['vehicle_id']} off-route for {vehicle['stop_duration']} minutes - Driver: {vehicle['driver_name']} ({vehicle['driver_phone']})",
            "location": {
                "lat": vehicle["latitude"],
                "lng": vehicle["longitude"],
                "description": get_nearest_landmark(vehicle["latitude"], vehicle["longitude"])
            },
            "timestamp": datetime.utcnow().isoformat(),
            "acknowledged": False,
            "requires_paging": True
        }
        incidents.append(incident)
    
    # Critical fuel level (<15%)
    if vehicle["fuel_level"] < 15:
        incident = {
            "id": f"CRITICAL_FUEL_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
            "vehicle_id": vehicle["vehicle_id"],
            "incident_type": "critical_low_fuel",
            "severity": "high",
            "message": f"URGENT: Vehicle {vehicle['vehicle_id']} critically low fuel: {vehicle['fuel_level']:.1f}% - Driver: {vehicle['driver_name']} ({vehicle['driver_phone']})",
            "location": {
                "lat": vehicle["latitude"],
                "lng": vehicle["longitude"],
                "description": get_nearest_landmark(vehicle["latitude"], vehicle["longitude"])
            },
            "timestamp": datetime.utcnow().isoformat(),
            "acknowledged": False,
            "requires_paging": False
        }
        incidents.append(incident)
    
    return incidents

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters"""
    R = 6371000
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon/2) * math.sin(delta_lon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def is_on_route(vehicle_lat, vehicle_lon, max_deviation=500):
    """Check if vehicle is on route"""
    route_waypoints = [
        {"latitude": 20.9463, "longitude": 85.2190, "name": "NTPC Talcher"},
        {"latitude": 20.9520, "longitude": 85.2380, "name": "Talcher Junction"},
        {"latitude": 20.9680, "longitude": 85.2890, "name": "Boinda"},
        {"latitude": 20.9850, "longitude": 85.3450, "name": "Dhenkanal Road"},
        {"latitude": 20.9950, "longitude": 85.4200, "name": "Dhenkanal"},
        {"latitude": 21.0100, "longitude": 85.5100, "name": "Kamakhyanagar"},
        {"latitude": 20.9800, "longitude": 85.6200, "name": "Parjang"},
        {"latitude": 20.9500, "longitude": 85.7800, "name": "Hindol Road"},
        {"latitude": 20.9200, "longitude": 85.8900, "name": "Bhuban"},
        {"latitude": 20.8950, "longitude": 86.0200, "name": "Jajpur Road"},
        {"latitude": 20.8739, "longitude": 86.0891, "name": "Chandilkhol Industrial Area"}
    ]
    
    for waypoint in route_waypoints:
        distance = calculate_distance(
            vehicle_lat, vehicle_lon,
            waypoint["latitude"], waypoint["longitude"]
        )
        if distance <= max_deviation:
            return True, waypoint["name"], distance
    return False, None, float('inf')

def get_nearest_landmark(lat, lng):
    """Get nearest landmark for location context"""
    waypoints = [
        {"latitude": 20.9463, "longitude": 85.2190, "name": "NTPC Talcher"},
        {"latitude": 20.9520, "longitude": 85.2380, "name": "Talcher Junction"},
        {"latitude": 20.9680, "longitude": 85.2890, "name": "Boinda"},
        {"latitude": 20.9850, "longitude": 85.3450, "name": "Dhenkanal Road"},
        {"latitude": 20.9950, "longitude": 85.4200, "name": "Dhenkanal"},
        {"latitude": 21.0100, "longitude": 85.5100, "name": "Kamakhyanagar"},
        {"latitude": 20.9800, "longitude": 85.6200, "name": "Parjang"},
        {"latitude": 20.9500, "longitude": 85.7800, "name": "Hindol Road"},
        {"latitude": 20.9200, "longitude": 85.8900, "name": "Bhuban"},
        {"latitude": 20.8950, "longitude": 86.0200, "name": "Jajpur Road"},
        {"latitude": 20.8739, "longitude": 86.0891, "name": "Chandilkhol Industrial Area"}
    ]
    
    min_distance = float('inf')
    nearest = "Unknown location"
    
    for waypoint in waypoints:
        distance = calculate_distance(lat, lng, waypoint["latitude"], waypoint["longitude"])
        if distance < min_distance:
            min_distance = distance
            nearest = waypoint["name"]
    
    return nearest

# API Routes
@app.get("/")
async def root():
    return {
        "message": "NTPC Fleet Management System - Critical Operations",
        "version": "4.0.0",
        "status": "operational",
        "features": [
            "Critical Incident Paging System",
            "Smart Gate Camera Integration",
            "Real-time Number Plate Recognition",
            "Emergency Contact Escalation",
            "Gate Entry/Exit Monitoring"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "total_vehicles": len(mock_vehicles),
        "critical_incidents": len([i for i in critical_incidents if i.get("severity") == "critical"]),
        "gate_cameras_active": len([c for c in PLANT_STOCKYARD["smart_cameras"] if c["active"]]),
        "paging_system": "operational"
    }

@app.get("/api/v1/vehicles/locations")
async def get_vehicle_locations():
    global critical_incidents
    
    for vehicle in mock_vehicles:
        # Simulate vehicle movement and tracking
        simulate_enhanced_vehicle_movement(vehicle)
        
        # Check for critical incidents
        new_incidents = check_critical_incidents(vehicle)
        for incident in new_incidents:
            # Check if this incident already exists
            existing = [i for i in critical_incidents if 
                       i["vehicle_id"] == incident["vehicle_id"] and 
                       i["incident_type"] == incident["incident_type"] and 
                       not i.get("acknowledged", False)]
            
            if not existing:
                critical_incidents.append(incident)
                
                # Trigger critical paging if required
                if incident.get("requires_paging", False):
                    paged_contacts = trigger_critical_incident_paging(incident)
                    incident["paged_contacts"] = paged_contacts
    
    return {
        "locations": mock_vehicles,
        "count": len(mock_vehicles)
    }

@app.get("/api/v1/incidents/critical")
async def get_critical_incidents():
    critical_only = [i for i in critical_incidents if i.get("severity") == "critical"]
    return {
        "incidents": critical_only,
        "count": len(critical_only)
    }

@app.get("/api/v1/gate/entries")
async def get_gate_entries():
    return {
        "entries": gate_entries,
        "count": len(gate_entries),
        "active_cameras": len([c for c in PLANT_STOCKYARD["smart_cameras"] if c["active"]])
    }

@app.post("/api/v1/gate/scan/{vehicle_id}")
async def simulate_gate_scan(vehicle_id: str):
    """Simulate smart camera scanning a vehicle at gate"""
    # Find the vehicle
    vehicle = next((v for v in mock_vehicles if v["vehicle_id"] == vehicle_id), None)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Simulate camera scan
    camera_data = simulate_smart_camera_scan(vehicle_id)
    
    # Create gate entry record
    gate_entry = {
        "id": f"GATE_{len(gate_entries) + 1:03d}",
        "vehicle_id": vehicle_id,
        "number_plate": vehicle["license_plate"],
        "driver_name": vehicle["driver_name"],
        "entry_time": datetime.utcnow().isoformat(),
        "exit_time": None,
        "camera_image": generate_mock_camera_image(),
        "gate_officer": f"Security Officer {random.choice(['Raman Das', 'Prakash Singh', 'Suresh Kumar', 'Amit Patel'])}",
        "load_weight": random.uniform(22.0, 26.0),
        "camera_scan_data": camera_data
    }
    
    gate_entries.append(gate_entry)
    
    # Update vehicle gate tracking
    vehicle["gate_entry_logged"] = True
    vehicle["last_gate_scan"] = datetime.utcnow().isoformat()
    
    return {
        "message": f"Gate scan completed for vehicle {vehicle_id}",
        "gate_entry": gate_entry,
        "camera_data": camera_data
    }

@app.post("/api/v1/incidents/{incident_id}/acknowledge")
async def acknowledge_critical_incident(incident_id: str):
    for incident in critical_incidents:
        if incident["id"] == incident_id:
            incident["acknowledged"] = True
            incident["acknowledged_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"✅ CRITICAL INCIDENT ACKNOWLEDGED:")
            logger.info(f"   🆔 ID: {incident_id}")
            logger.info(f"   🚛 Vehicle: {incident['vehicle_id']}")
            logger.info(f"   ⚠️  Type: {incident['incident_type']}")
            
            return {"message": "Critical incident acknowledged", "incident": incident}
    
    raise HTTPException(status_code=404, detail="Incident not found")

@app.get("/api/v1/cameras/status")
async def get_camera_status():
    return {
        "cameras": PLANT_STOCKYARD["smart_cameras"],
        "total_cameras": len(PLANT_STOCKYARD["smart_cameras"]),
        "active_cameras": len([c for c in PLANT_STOCKYARD["smart_cameras"] if c["active"]]),
        "last_scan": datetime.utcnow().isoformat()
    }

def generate_mock_camera_image():
    """Generate mock base64 camera image"""
    # This would be replaced with actual camera feed in production
    return "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD//gA7Q1JFQVRPUjogZ2QtanBlZyB2MS4wICh1c2luZyBJSkcgSlBFRyB2NjIpLCBxdWFsaXR5ID0gODAK/9sAQwAIBgYHBgUIBwcHCQkICgwUDQwLCwwZEhMPFB0aHx4dGhwcICQuJyAiLCMcHCg3KSwwMTQ0NB8nOT04MjwuMzQy"

def simulate_enhanced_vehicle_movement(vehicle):
    """Enhanced vehicle simulation with gate tracking"""
    if vehicle["route_status"] == "on_route" and vehicle["speed"] > 0:
        progress = vehicle["route_progress"]
        if progress < 100:
            base_progress = random.uniform(0.3, 1.5)
            vehicle["route_progress"] = min(progress + base_progress, 100)
            
            # Update position
            if vehicle["route_progress"] < 100:
                # Simulate movement along route
                vehicle["latitude"] += random.uniform(-0.0001, 0.0001)
                vehicle["longitude"] += random.uniform(-0.0001, 0.0001)
    
    # Add realistic variation
    if vehicle["speed"] > 0:
        vehicle["speed"] = max(0, vehicle["speed"] + random.uniform(-8, 8))
        vehicle["fuel_level"] = max(0, vehicle["fuel_level"] - random.uniform(0.1, 0.3))
    
    # Update stop duration
    if vehicle["speed"] == 0:
        last_movement = datetime.fromisoformat(vehicle["last_movement"].replace('Z', '+00:00'))
        vehicle["stop_duration"] = int((datetime.utcnow() - last_movement.replace(tzinfo=None)).total_seconds() / 60)
        
        # Update route status based on stop duration
        if vehicle["stop_duration"] > 60:
            vehicle["route_status"] = "critical_stop"
    else:
        vehicle["last_movement"] = datetime.utcnow().isoformat()
        vehicle["stop_duration"] = 0
        if vehicle["route_status"] == "critical_stop":
            vehicle["route_status"] = "on_route"
    
    # Update route status based on speed
    if vehicle["speed"] > 90:
        vehicle["route_status"] = "critical_speed"
    elif vehicle["speed"] > 80:
        vehicle["route_status"] = "speed_violation"
    elif vehicle["route_status"] in ["critical_speed", "speed_violation"] and vehicle["speed"] <= 80:
        vehicle["route_status"] = "on_route"
    
    vehicle["timestamp"] = datetime.utcnow().isoformat()

# Background monitoring for critical incidents
async def critical_incident_monitoring():
    """Enhanced background monitoring with critical incident detection"""
    while True:
        try:
            for vehicle in mock_vehicles:
                incidents = check_critical_incidents(vehicle)
                for incident in incidents:
                    existing = [i for i in critical_incidents if 
                              i["vehicle_id"] == incident["vehicle_id"] and 
                              i["incident_type"] == incident["incident_type"] and 
                              not i.get("acknowledged", False)]
                    
                    if not existing:
                        critical_incidents.append(incident)
                        
                        # Immediate paging for critical incidents
                        if incident.get("requires_paging", False):
                            paged_contacts = trigger_critical_incident_paging(incident)
                            incident["paged_contacts"] = paged_contacts
            
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Error in critical incident monitoring: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(critical_incident_monitoring())
    logger.info("🚨 NTPC Critical Fleet Management System Started")
    logger.info("📟 Critical incident paging system: ACTIVE")
    logger.info("📷 Smart gate cameras: OPERATIONAL")
    logger.info(f"🎯 Active cameras: {len([c for c in PLANT_STOCKYARD['smart_cameras'] if c['active']])}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005, reload=True)
