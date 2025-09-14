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
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NTPC Fleet Management System - India",
    description="Advanced fleet management for NTPC Talcher to Chandilkhol route with comprehensive monitoring",
    version="3.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# India Route Configuration - NTPC Talcher to Chandilkhol
PLANT_STOCKYARD = {
    "latitude": 20.9463,
    "longitude": 85.2190,
    "name": "NTPC Talcher Super Thermal Power Station",
    "address": "Talcher, Angul, Odisha, India",
    "radius": 200  # meters
}

DESTINATION = {
    "latitude": 20.8739,
    "longitude": 86.0891,
    "name": "Chandilkhol Industrial Area",
    "address": "Chandilkhol, Jajpur, Odisha, India", 
    "radius": 200  # meters
}

# Predefined route waypoints (NTPC Talcher to Chandilkhol via NH16 and SH9A)
ROUTE_WAYPOINTS = [
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

# Points of Interest (Gas Stations, Toll Gates)
POIS = [
    {"type": "gas_station", "name": "HP Petrol Pump Talcher", "latitude": 20.9480, "longitude": 85.2250},
    {"type": "gas_station", "name": "Indian Oil Boinda", "latitude": 20.9690, "longitude": 85.2910},
    {"type": "toll_gate", "name": "Dhenkanal Toll Plaza", "latitude": 20.9900, "longitude": 85.4150},
    {"type": "gas_station", "name": "Bharat Petroleum Dhenkanal", "latitude": 20.9920, "longitude": 85.4180},
    {"type": "gas_station", "name": "HP Petrol Pump Kamakhyanagar", "latitude": 21.0120, "longitude": 85.5120},
    {"type": "toll_gate", "name": "Parjang Toll Plaza", "latitude": 20.9780, "longitude": 85.6180},
    {"type": "gas_station", "name": "Indian Oil Hindol", "latitude": 20.9520, "longitude": 85.7820},
    {"type": "gas_station", "name": "Reliance Petrol Bhuban", "latitude": 20.9180, "longitude": 85.8920},
    {"type": "toll_gate", "name": "Jajpur Road Toll Plaza", "latitude": 20.8970, "longitude": 86.0180},
    {"type": "gas_station", "name": "HP Petrol Pump Chandilkhol", "latitude": 20.8760, "longitude": 86.0870}
]

# Enhanced mock vehicles - 13 trucks total
mock_vehicles = [
    {
        "id": 1, "vehicle_id": "OD-03-NT-1001", "driver_name": "Rajesh Kumar", "driver_phone": "+91-9437123001",
        "license_plate": "OD-03-NT-1001", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9463, "longitude": 85.2190, "speed": 0, "heading": 90,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-13T15:30:00", "route_progress": 5, "fuel_level": 85
    },
    {
        "id": 2, "vehicle_id": "OD-03-NT-1002", "driver_name": "Santosh Patel", "driver_phone": "+91-9437123002",
        "license_plate": "OD-03-NT-1002", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9680, "longitude": 85.2890, "speed": 45, "heading": 85,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-13T15:15:00", "route_progress": 25, "fuel_level": 78
    },
    {
        "id": 3, "vehicle_id": "OD-03-NT-1003", "driver_name": "Manoj Behera", "driver_phone": "+91-9437123003",
        "license_plate": "OD-03-NT-1003", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9950, "longitude": 85.4200, "speed": 0, "heading": 90,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "stopped", "stop_duration": 45, "last_movement": (datetime.utcnow() - timedelta(minutes=45)).isoformat(),
        "destination_eta": "2025-09-13T16:00:00", "route_progress": 45, "fuel_level": 65
    },
    {
        "id": 4, "vehicle_id": "OD-03-NT-1004", "driver_name": "Sushant Jena", "driver_phone": "+91-9437123004",
        "license_plate": "OD-03-NT-1004", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 21.0100, "longitude": 85.5100, "speed": 55, "heading": 80,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-13T14:45:00", "route_progress": 55, "fuel_level": 72
    },
    {
        "id": 5, "vehicle_id": "OD-03-NT-1005", "driver_name": "Biswajit Nayak", "driver_phone": "+91-9437123005",
        "license_plate": "OD-03-NT-1005", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9800, "longitude": 85.6200, "speed": 35, "heading": 75,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-13T14:30:00", "route_progress": 65, "fuel_level": 58
    },
    {
        "id": 6, "vehicle_id": "OD-03-NT-1006", "driver_name": "Pradeep Mishra", "driver_phone": "+91-9437123006",
        "license_plate": "OD-03-NT-1006", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9500, "longitude": 85.7800, "speed": 0, "heading": 85,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "deviation", "stop_duration": 20, "last_movement": (datetime.utcnow() - timedelta(minutes=20)).isoformat(),
        "destination_eta": "2025-09-13T15:45:00", "route_progress": 75, "fuel_level": 45
    },
    {
        "id": 7, "vehicle_id": "OD-03-NT-1007", "driver_name": "Ajay Kumar Das", "driver_phone": "+91-9437123007",
        "license_plate": "OD-03-NT-1007", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9200, "longitude": 85.8900, "speed": 60, "heading": 80,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-13T14:20:00", "route_progress": 85, "fuel_level": 40
    },
    {
        "id": 8, "vehicle_id": "OD-03-NT-1008", "driver_name": "Rakesh Sahoo", "driver_phone": "+91-9437123008",
        "license_plate": "OD-03-NT-1008", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.8950, "longitude": 86.0200, "speed": 40, "heading": 85,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-13T14:10:00", "route_progress": 92, "fuel_level": 35
    },
    {
        "id": 9, "vehicle_id": "OD-03-NT-1009", "driver_name": "Subrat Mohanty", "driver_phone": "+91-9437123009",
        "license_plate": "OD-03-NT-1009", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.8739, "longitude": 86.0891, "speed": 0, "heading": 90,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": False, "load_status": "unloading",
        "route_status": "arrived", "stop_duration": 15, "last_movement": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
        "destination_eta": "2025-09-13T14:00:00", "route_progress": 100, "fuel_level": 25
    },
    {
        "id": 10, "vehicle_id": "OD-03-NT-1010", "driver_name": "Niranjan Swain", "driver_phone": "+91-9437123010",
        "license_plate": "OD-03-NT-1010", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9463, "longitude": 85.2190, "speed": 0, "heading": 90,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": False, "load_status": "loading",
        "route_status": "loading", "stop_duration": 25, "last_movement": (datetime.utcnow() - timedelta(minutes=25)).isoformat(),
        "destination_eta": "2025-09-13T16:15:00", "route_progress": 0, "fuel_level": 90
    },
    {
        "id": 11, "vehicle_id": "OD-03-NT-1011", "driver_name": "Tapan Kumar Rout", "driver_phone": "+91-9437123011",
        "license_plate": "OD-03-NT-1011", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9520, "longitude": 85.2380, "speed": 25, "heading": 85,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-13T15:45:00", "route_progress": 15, "fuel_level": 82
    },
    {
        "id": 12, "vehicle_id": "OD-03-NT-1012", "driver_name": "Surya Narayan Padhi", "driver_phone": "+91-9437123012",
        "license_plate": "OD-03-NT-1012", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9850, "longitude": 85.3450, "speed": 85, "heading": 80,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "speed_violation", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-13T14:25:00", "route_progress": 35, "fuel_level": 70
    },
    {
        "id": 13, "vehicle_id": "OD-03-NT-1013", "driver_name": "Dillip Kumar Sahu", "driver_phone": "+91-9437123013",
        "license_plate": "OD-03-NT-1013", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 21.0200, "longitude": 85.4800, "speed": 0, "heading": 85,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "deviation", "stop_duration": 55, "last_movement": (datetime.utcnow() - timedelta(minutes=55)).isoformat(),
        "destination_eta": "2025-09-13T16:30:00", "route_progress": 50, "fuel_level": 60
    }
]

# Alert storage and stakeholder contacts
active_alerts = []
stakeholder_contacts = [
    {"name": "Fleet Manager", "phone": "+91-9437100001", "email": "fleet.manager@ntpc.co.in", "role": "manager"},
    {"name": "IT Supervisor", "phone": "+91-9437100002", "email": "it.supervisor@ntpc.co.in", "role": "it"},
    {"name": "Operations Head", "phone": "+91-9437100003", "email": "operations.head@ntpc.co.in", "role": "operations"},
    {"name": "Safety Officer", "phone": "+91-9437100004", "email": "safety.officer@ntpc.co.in", "role": "safety"}
]

# Enhanced utility functions
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters using Haversine formula"""
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

def is_on_route(vehicle_lat, vehicle_lon, max_deviation=500):
    """Enhanced route checking with better tolerance for Indian roads"""
    for i, waypoint in enumerate(ROUTE_WAYPOINTS):
        distance = calculate_distance(
            vehicle_lat, vehicle_lon,
            waypoint["latitude"], waypoint["longitude"]
        )
        if distance <= max_deviation:
            return True, waypoint["name"], distance
    return False, None, float('inf')

def get_speed_limit_for_location(latitude, longitude):
    """Get speed limit based on location (highway vs city)"""
    # NH16 and major highways: 80 km/h for trucks
    # City areas: 50 km/h
    # Near toll gates/intersections: 40 km/h
    
    for poi in POIS:
        if poi["type"] == "toll_gate":
            distance = calculate_distance(latitude, longitude, poi["latitude"], poi["longitude"])
            if distance < 2000:  # Within 2km of toll gate
                return 40
    
    # Check if in city area (near major waypoints)
    city_waypoints = ["NTPC Talcher", "Dhenkanal", "Chandilkhol Industrial Area"]
    for waypoint in ROUTE_WAYPOINTS:
        if waypoint["name"] in city_waypoints:
            distance = calculate_distance(latitude, longitude, waypoint["latitude"], waypoint["longitude"])
            if distance < 5000:  # Within 5km of city
                return 50
    
    return 80  # Highway speed limit

def check_enhanced_alerts(vehicle):
    """Enhanced alert system with detailed categorization"""
    alerts = []
    
    # Extended stop alert (>30 minutes)
    if vehicle["speed"] == 0 and vehicle["stop_duration"] > 30:
        severity = "critical" if vehicle["stop_duration"] > 60 else "high"
        alerts.append({
            "id": f"extended_stop_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
            "vehicle_id": vehicle["vehicle_id"],
            "alert_type": "extended_stop",
            "message": f"Vehicle {vehicle['vehicle_id']} stopped for {vehicle['stop_duration']} minutes at {get_nearest_landmark(vehicle['latitude'], vehicle['longitude'])}",
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active",
            "driver_phone": vehicle["driver_phone"],
            "location": {"lat": vehicle["latitude"], "lng": vehicle["longitude"]}
        })
    
    # Route deviation alert
    on_route, nearest_waypoint, deviation_distance = is_on_route(vehicle["latitude"], vehicle["longitude"])
    if not on_route and vehicle["route_status"] != "loading" and vehicle["route_status"] != "arrived":
        alerts.append({
            "id": f"route_deviation_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
            "vehicle_id": vehicle["vehicle_id"],
            "alert_type": "route_deviation",
            "message": f"Vehicle {vehicle['vehicle_id']} deviated {deviation_distance:.0f}m from route near {get_nearest_landmark(vehicle['latitude'], vehicle['longitude'])}",
            "severity": "high",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active",
            "driver_phone": vehicle["driver_phone"],
            "location": {"lat": vehicle["latitude"], "lng": vehicle["longitude"]}
        })
    
    # Enhanced speed violation alert
    speed_limit = get_speed_limit_for_location(vehicle["latitude"], vehicle["longitude"])
    if vehicle["speed"] > speed_limit:
        excess_speed = vehicle["speed"] - speed_limit
        severity = "critical" if excess_speed > 20 else "high" if excess_speed > 10 else "medium"
        alerts.append({
            "id": f"speed_violation_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
            "vehicle_id": vehicle["vehicle_id"],
            "alert_type": "speed_violation",
            "message": f"Vehicle {vehicle['vehicle_id']} exceeding speed limit by {excess_speed:.1f} km/h (Current: {vehicle['speed']:.1f}, Limit: {speed_limit}) near {get_nearest_landmark(vehicle['latitude'], vehicle['longitude'])}",
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active",
            "driver_phone": vehicle["driver_phone"],
            "location": {"lat": vehicle["latitude"], "lng": vehicle["longitude"]}
        })
    
    # Low fuel alert
    if vehicle["fuel_level"] < 30:
        severity = "critical" if vehicle["fuel_level"] < 15 else "medium"
        nearest_gas_station = get_nearest_gas_station(vehicle["latitude"], vehicle["longitude"])
        alerts.append({
            "id": f"low_fuel_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
            "vehicle_id": vehicle["vehicle_id"],
            "alert_type": "low_fuel",
            "message": f"Vehicle {vehicle['vehicle_id']} low fuel: {vehicle['fuel_level']}%. Nearest gas station: {nearest_gas_station['name']} ({nearest_gas_station['distance']:.1f}km)",
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active",
            "driver_phone": vehicle["driver_phone"],
            "location": {"lat": vehicle["latitude"], "lng": vehicle["longitude"]}
        })
    
    return alerts

def get_nearest_landmark(lat, lng):
    """Get nearest landmark for location context"""
    min_distance = float('inf')
    nearest = "Unknown location"
    
    for waypoint in ROUTE_WAYPOINTS:
        distance = calculate_distance(lat, lng, waypoint["latitude"], waypoint["longitude"])
        if distance < min_distance:
            min_distance = distance
            nearest = waypoint["name"]
    
    return nearest

def get_nearest_gas_station(lat, lng):
    """Find nearest gas station"""
    min_distance = float('inf')
    nearest = None
    
    for poi in POIS:
        if poi["type"] == "gas_station":
            distance = calculate_distance(lat, lng, poi["latitude"], poi["longitude"]) / 1000  # Convert to km
            if distance < min_distance:
                min_distance = distance
                nearest = {"name": poi["name"], "distance": distance}
    
    return nearest or {"name": "No gas station found", "distance": 0}

def simulate_enhanced_vehicle_movement(vehicle):
    """Enhanced vehicle simulation with realistic Indian road conditions"""
    if vehicle["route_status"] == "on_route" and vehicle["speed"] > 0:
        # Simulate progress along route
        progress = vehicle["route_progress"]
        if progress < 100:
            # Account for traffic, road conditions, etc.
            base_progress = random.uniform(0.3, 1.5)
            
            # Reduce progress near toll gates (traffic slowdown)
            for poi in POIS:
                if poi["type"] == "toll_gate":
                    distance = calculate_distance(vehicle["latitude"], vehicle["longitude"], poi["latitude"], poi["longitude"])
                    if distance < 3000:  # Within 3km of toll gate
                        base_progress *= 0.5
            
            vehicle["route_progress"] = min(progress + base_progress, 100)
            
            # Update position along route
            if vehicle["route_progress"] < 100:
                total_waypoints = len(ROUTE_WAYPOINTS) - 1
                current_segment = int((vehicle["route_progress"] / 100) * total_waypoints)
                current_segment = min(current_segment, total_waypoints - 1)
                
                start_point = ROUTE_WAYPOINTS[current_segment]
                end_point = ROUTE_WAYPOINTS[current_segment + 1]
                
                segment_progress = ((vehicle["route_progress"] / 100) * total_waypoints) - current_segment
                
                vehicle["latitude"] = (start_point["latitude"] + 
                                    (end_point["latitude"] - start_point["latitude"]) * segment_progress)
                vehicle["longitude"] = (start_point["longitude"] + 
                                      (end_point["longitude"] - start_point["longitude"]) * segment_progress)
    
    # Add realistic variation
    if vehicle["speed"] > 0:
        vehicle["latitude"] += random.uniform(-0.0001, 0.0001)
        vehicle["longitude"] += random.uniform(-0.0001, 0.0001)
        vehicle["speed"] = max(0, vehicle["speed"] + random.uniform(-8, 8))
        vehicle["fuel_level"] = max(0, vehicle["fuel_level"] - random.uniform(0.1, 0.3))
    
    # Update stop duration and movement
    if vehicle["speed"] == 0:
        last_movement = datetime.fromisoformat(vehicle["last_movement"].replace('Z', '+00:00'))
        vehicle["stop_duration"] = int((datetime.utcnow() - last_movement.replace(tzinfo=None)).total_seconds() / 60)
    else:
        vehicle["last_movement"] = datetime.utcnow().isoformat()
        vehicle["stop_duration"] = 0
    
    vehicle["timestamp"] = datetime.utcnow().isoformat()

# Mock SMS/Email notification service
async def send_mobile_alert(alert, contact):
    """Mock mobile alert system - would integrate with SMS/Email APIs"""
    logger.info(f"📱 MOBILE ALERT SENT:")
    logger.info(f"   To: {contact['name']} ({contact['phone']}) - {contact['email']}")
    logger.info(f"   Alert: {alert['alert_type'].upper()}")
    logger.info(f"   Vehicle: {alert['vehicle_id']}")
    logger.info(f"   Message: {alert['message']}")
    logger.info(f"   Severity: {alert['severity'].upper()}")
    
    # In production, you would integrate with:
    # - SMS API (Twilio, AWS SNS, etc.)
    # - Email API (SendGrid, AWS SES, etc.)
    # - Push notification services (Firebase, OneSignal, etc.)

# API Routes
@app.get("/")
async def root():
    return {
        "message": "NTPC Fleet Management System - India Operations",
        "version": "3.0.0",
        "route": "NTPC Talcher → Chandilkhol",
        "status": "operational",
        "features": [
            "13 Vehicle Fleet Tracking",
            "Enhanced Speed & Route Monitoring", 
            "Mobile Alert System",
            "Gas Station & Toll Gate Mapping",
            "Real-time Deviation Detection"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "total_vehicles": len(mock_vehicles),
        "active_alerts": len([a for a in active_alerts if a["status"] == "active"]),
        "route_distance": "~85 km",
        "average_trip_time": "2.5 hours"
    }

@app.get("/api/v1/vehicles/")
async def get_vehicles():
    return {
        "vehicles": mock_vehicles,
        "count": len(mock_vehicles),
        "route": f"{PLANT_STOCKYARD['name']} → {DESTINATION['name']}"
    }

@app.get("/api/v1/vehicles/locations")
async def get_vehicle_locations():
    global active_alerts
    
    for vehicle in mock_vehicles:
        simulate_enhanced_vehicle_movement(vehicle)
        
        # Check for alerts
        new_alerts = check_enhanced_alerts(vehicle)
        for alert in new_alerts:
            # Avoid duplicate alerts
            existing = [a for a in active_alerts if 
                       a["vehicle_id"] == alert["vehicle_id"] and 
                       a["alert_type"] == alert["alert_type"] and 
                       a["status"] == "active"]
            if not existing:
                active_alerts.append(alert)
                
                # Send mobile alerts to stakeholders
                for contact in stakeholder_contacts:
                    if (alert["severity"] in ["critical", "high"]) or contact["role"] == "it":
                        await send_mobile_alert(alert, contact)
    
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
        "pois": POIS,
        "total_distance_km": 85.2,
        "estimated_time_hours": 2.5,
        "route_description": "NTPC Talcher to Chandilkhol via NH16 and SH9A"
    }

@app.get("/api/v1/alerts/")
async def get_alerts(status: str = "active"):
    filtered_alerts = [a for a in active_alerts if a["status"] == status]
    return {
        "alerts": filtered_alerts,
        "count": len(filtered_alerts)
    }

@app.get("/api/v1/analytics/summary")
async def get_analytics_summary():
    total_vehicles = len(mock_vehicles)
    on_route = len([v for v in mock_vehicles if v["route_status"] == "on_route"])
    stopped = len([v for v in mock_vehicles if v["route_status"] == "stopped"])
    loaded_vehicles = len([v for v in mock_vehicles if v["material_loaded"]])
    speed_violations = len([v for v in mock_vehicles if v["route_status"] == "speed_violation"])
    deviations = len([v for v in mock_vehicles if v["route_status"] == "deviation"])
    
    return {
        "total_vehicles": total_vehicles,
        "on_route": on_route,
        "stopped": stopped,
        "deviations": deviations,
        "speed_violations": speed_violations,
        "loaded_vehicles": loaded_vehicles,
        "active_alerts": len([a for a in active_alerts if a["status"] == "active"]),
        "average_progress": sum([v["route_progress"] for v in mock_vehicles]) / total_vehicles,
        "average_fuel_level": sum([v["fuel_level"] for v in mock_vehicles]) / total_vehicles,
        "route_efficiency": ((on_route / total_vehicles) * 100) if total_vehicles > 0 else 0,
        "generated_at": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    for alert in active_alerts:
        if alert["id"] == alert_id:
            alert["status"] = "acknowledged"
            alert["acknowledged_at"] = datetime.utcnow().isoformat()
            return {"message": "Alert acknowledged", "alert": alert}
    return {"error": "Alert not found"}, 404

# Background monitoring with enhanced alert system
async def enhanced_fleet_monitoring():
    """Enhanced background monitoring for Indian operations"""
    while True:
        try:
            for vehicle in mock_vehicles:
                alerts = check_enhanced_alerts(vehicle)
                for alert in alerts:
                    existing = [a for a in active_alerts if 
                              a["vehicle_id"] == alert["vehicle_id"] and 
                              a["alert_type"] == alert["alert_type"] and 
                              a["status"] == "active"]
                    if not existing:
                        active_alerts.append(alert)
                        
                        # Send critical alerts immediately
                        if alert["severity"] == "critical":
                            for contact in stakeholder_contacts:
                                await send_mobile_alert(alert, contact)
            
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in enhanced fleet monitoring: {e}")
            await asyncio.sleep(120)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(enhanced_fleet_monitoring())
    logger.info("🇮🇳 NTPC Fleet Management System - India Operations Started")
    logger.info(f"📍 Route: {PLANT_STOCKYARD['name']} → {DESTINATION['name']}")
    logger.info(f"🚛 Fleet Size: {len(mock_vehicles)} vehicles")
    logger.info("📱 Mobile alert system activated")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004, reload=True)
