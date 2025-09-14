import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import random
import math
import requests
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NTPC Fleet Management System - Enhanced India Operations",
    description="Advanced fleet management with PagerDuty-style escalation and Smart Gate integration",
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
class PagerDutyIncident(BaseModel):
    id: str
    vehicle_id: str
    incident_type: str
    severity: str
    message: str
    location: dict
    timestamp: str
    escalation_level: int
    contact_attempts: List[dict]
    acknowledged: bool
    escalation_timeout: int  # minutes

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
    ai_confidence: float

# Enhanced India Route Configuration - NTPC Talcher to Chandilkhol
PLANT_STOCKYARD = {
    "latitude": 20.9463,
    "longitude": 85.2190,
    "name": "NTPC Talcher Super Thermal Power Station",
    "address": "Talcher, Angul, Odisha, India",
    "radius": 200,  # meters
    "smart_cameras": [
        {"id": "CAM_GATE_01", "location": "Main Entry Gate", "active": True, "ai_enabled": True},
        {"id": "CAM_GATE_02", "location": "Secondary Gate", "active": True, "ai_enabled": True},
        {"id": "CAM_LOAD_01", "location": "Loading Bay A", "active": True, "ai_enabled": True},
        {"id": "CAM_LOAD_02", "location": "Loading Bay B", "active": True, "ai_enabled": True}
    ]
}

DESTINATION = {
    "latitude": 20.8739,
    "longitude": 86.0891,
    "name": "Chandilkhol Industrial Area",
    "address": "Chandilkhol, Jajpur, Odisha, India", 
    "radius": 200  # meters
}

# PagerDuty-style escalation contacts with detailed escalation policy
ESCALATION_CONTACTS = [
    {
        "name": "Fleet Manager", 
        "phone": "+91-9437100001", 
        "email": "fleet.manager@ntpc.co.in", 
        "push_token": "fleet_mgr_push_001",
        "role": "primary",
        "escalation_level": 1,
        "escalation_timeout": 5  # minutes before escalating
    },
    {
        "name": "IT Emergency Team", 
        "phone": "+91-9437100002", 
        "email": "it.emergency@ntpc.co.in", 
        "push_token": "it_emergency_push_002",
        "role": "primary",
        "escalation_level": 1,
        "escalation_timeout": 5
    },
    {
        "name": "Operations Control Room", 
        "phone": "+91-9437100003", 
        "email": "operations.control@ntpc.co.in", 
        "push_token": "ops_control_push_003",
        "role": "primary",
        "escalation_level": 1,
        "escalation_timeout": 5
    },
    {
        "name": "Safety Emergency Team", 
        "phone": "+91-9437100004", 
        "email": "safety.emergency@ntpc.co.in", 
        "push_token": "safety_emergency_push_004",
        "role": "primary",
        "escalation_level": 1,
        "escalation_timeout": 5
    },
    {
        "name": "Plant Security Chief", 
        "phone": "+91-9437100005", 
        "email": "security.chief@ntpc.co.in", 
        "push_token": "security_chief_push_005",
        "role": "secondary",
        "escalation_level": 2,
        "escalation_timeout": 3
    },
    {
        "name": "Transport Supervisor", 
        "phone": "+91-9437100006", 
        "email": "transport.supervisor@ntpc.co.in", 
        "push_token": "transport_sup_push_006",
        "role": "secondary",
        "escalation_level": 2,
        "escalation_timeout": 3
    },
    {
        "name": "Emergency Coordinator", 
        "phone": "+91-9437100007", 
        "email": "emergency.coordinator@ntpc.co.in", 
        "push_token": "emergency_coord_push_007",
        "role": "escalation",
        "escalation_level": 3,
        "escalation_timeout": 2
    }
]

# Predefined route waypoints (NTPC Talcher to Chandilkhol via NH16 and SH9A)
ROUTE_WAYPOINTS = [
    {"latitude": 20.9463, "longitude": 85.2190, "name": "NTPC Talcher", "speed_limit": 40},
    {"latitude": 20.9520, "longitude": 85.2380, "name": "Talcher Junction", "speed_limit": 50},
    {"latitude": 20.9680, "longitude": 85.2890, "name": "Boinda", "speed_limit": 80},
    {"latitude": 20.9850, "longitude": 85.3450, "name": "Dhenkanal Road", "speed_limit": 80},
    {"latitude": 20.9950, "longitude": 85.4200, "name": "Dhenkanal", "speed_limit": 50},
    {"latitude": 21.0100, "longitude": 85.5100, "name": "Kamakhyanagar", "speed_limit": 80},
    {"latitude": 20.9800, "longitude": 85.6200, "name": "Parjang", "speed_limit": 80},
    {"latitude": 20.9500, "longitude": 85.7800, "name": "Hindol Road", "speed_limit": 80},
    {"latitude": 20.9200, "longitude": 85.8900, "name": "Bhuban", "speed_limit": 50},
    {"latitude": 20.8950, "longitude": 86.0200, "name": "Jajpur Road", "speed_limit": 50},
    {"latitude": 20.8739, "longitude": 86.0891, "name": "Chandilkhol Industrial Area", "speed_limit": 40}
]

# Enhanced mock vehicles - ALL 13 heavy coal transport trucks
mock_vehicles = [
    {
        "id": 1, "vehicle_id": "OD-03-NT-1001", "driver_name": "Rajesh Kumar", "driver_phone": "+91-9437123001",
        "license_plate": "OD-03-NT-1001", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9463, "longitude": 85.2190, "speed": 0, "heading": 90,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-14T15:30:00", "route_progress": 5, "fuel_level": 85,
        "gate_entry_logged": True, "last_gate_scan": datetime.utcnow().isoformat()
    },
    {
        "id": 2, "vehicle_id": "OD-03-NT-1002", "driver_name": "Santosh Patel", "driver_phone": "+91-9437123002",
        "license_plate": "OD-03-NT-1002", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9680, "longitude": 85.2890, "speed": 45, "heading": 85,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-14T15:15:00", "route_progress": 25, "fuel_level": 78,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(minutes=30)).isoformat()
    },
    {
        "id": 3, "vehicle_id": "OD-03-NT-1003", "driver_name": "Manoj Behera", "driver_phone": "+91-9437123003",
        "license_plate": "OD-03-NT-1003", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9950, "longitude": 85.4200, "speed": 0, "heading": 90,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "critical_stop", "stop_duration": 65, "last_movement": (datetime.utcnow() - timedelta(minutes=65)).isoformat(),
        "destination_eta": "2025-09-14T16:00:00", "route_progress": 45, "fuel_level": 65,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=1)).isoformat()
    },
    {
        "id": 4, "vehicle_id": "OD-03-NT-1004", "driver_name": "Sushant Jena", "driver_phone": "+91-9437123004",
        "license_plate": "OD-03-NT-1004", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 21.0500, "longitude": 85.5500, "speed": 95, "heading": 80,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "critical_speed", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-14T14:45:00", "route_progress": 55, "fuel_level": 72,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=1, minutes=15)).isoformat()
    },
    {
        "id": 5, "vehicle_id": "OD-03-NT-1005", "driver_name": "Prakash Mohanty", "driver_phone": "+91-9437123005",
        "license_plate": "OD-03-NT-1005", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9200, "longitude": 85.8900, "speed": 55, "heading": 95,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-14T14:30:00", "route_progress": 75, "fuel_level": 40,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=2)).isoformat()
    },
    {
        "id": 6, "vehicle_id": "OD-03-NT-1006", "driver_name": "Deepak Singh", "driver_phone": "+91-9437123006",
        "license_plate": "OD-03-NT-1006", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.8950, "longitude": 86.0200, "speed": 60, "heading": 88,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-14T14:15:00", "route_progress": 85, "fuel_level": 35,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=2, minutes=30)).isoformat()
    },
    {
        "id": 7, "vehicle_id": "OD-03-NT-1007", "driver_name": "Ravi Mishra", "driver_phone": "+91-9437123007",
        "license_plate": "OD-03-NT-1007", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 21.0100, "longitude": 85.5100, "speed": 0, "heading": 90,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "stopped", "stop_duration": 45, "last_movement": (datetime.utcnow() - timedelta(minutes=45)).isoformat(),
        "destination_eta": "2025-09-14T15:45:00", "route_progress": 50, "fuel_level": 55,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=1, minutes=30)).isoformat()
    },
    {
        "id": 8, "vehicle_id": "OD-03-NT-1008", "driver_name": "Anil Kumar", "driver_phone": "+91-9437123008",
        "license_plate": "OD-03-NT-1008", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9800, "longitude": 85.6200, "speed": 75, "heading": 92,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-14T15:00:00", "route_progress": 65, "fuel_level": 68,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=1, minutes=45)).isoformat()
    },
    {
        "id": 9, "vehicle_id": "OD-03-NT-1009", "driver_name": "Suresh Panda", "driver_phone": "+91-9437123009",
        "license_plate": "OD-03-NT-1009", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9500, "longitude": 85.7800, "speed": 82, "heading": 87,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "speed_violation", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-14T14:45:00", "route_progress": 70, "fuel_level": 48,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=2)).isoformat()
    },
    {
        "id": 10, "vehicle_id": "OD-03-NT-1010", "driver_name": "Biswa Nath", "driver_phone": "+91-9437123010",
        "license_plate": "OD-03-NT-1010", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.8739, "longitude": 86.0891, "speed": 0, "heading": 0,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": False, "load_status": "unloading",
        "route_status": "arrived", "stop_duration": 15, "last_movement": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
        "destination_eta": "2025-09-14T13:30:00", "route_progress": 100, "fuel_level": 25,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=3)).isoformat()
    },
    {
        "id": 11, "vehicle_id": "OD-03-NT-1011", "driver_name": "Kailash Das", "driver_phone": "+91-9437123011",
        "license_plate": "OD-03-NT-1011", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9520, "longitude": 85.2380, "speed": 35, "heading": 75,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-14T16:15:00", "route_progress": 15, "fuel_level": 90,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    },
    {
        "id": 12, "vehicle_id": "OD-03-NT-1012", "driver_name": "Ramesh Sahoo", "driver_phone": "+91-9437123012",
        "license_plate": "OD-03-NT-1012", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9850, "longitude": 85.3450, "speed": 85, "heading": 85,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "speed_violation", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-14T15:30:00", "route_progress": 35, "fuel_level": 62,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=1)).isoformat()
    },
    {
        "id": 13, "vehicle_id": "OD-03-NT-1013", "driver_name": "Subash Jena", "driver_phone": "+91-9437123013",
        "license_plate": "OD-03-NT-1013", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 21.0250, "longitude": 85.4850, "speed": 0, "heading": 90,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "deviation", "stop_duration": 55, "last_movement": (datetime.utcnow() - timedelta(minutes=55)).isoformat(),
        "destination_eta": "2025-09-14T16:45:00", "route_progress": 42, "fuel_level": 38,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=1, minutes=20)).isoformat()
    },
    # Truck 14 - Return journey
    {
        "id": 14, "vehicle_id": "OD-03-NT-1014", "driver_name": "Girish Mohanty", "driver_phone": "+91-9437123014",
        "license_plate": "OD-03-NT-1014", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9300, "longitude": 85.8400, "speed": 55, "heading": 270,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": False, "load_status": "empty",
        "route_status": "returning", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-14T16:30:00", "route_progress": 20, "fuel_level": 48,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=3)).isoformat()
    },
    # Truck 15 - Loading at plant
    {
        "id": 15, "vehicle_id": "OD-03-NT-1015", "driver_name": "Ashok Pradhan", "driver_phone": "+91-9437123015",
        "license_plate": "OD-03-NT-1015", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9600, "longitude": 85.2650, "speed": 0, "heading": 90,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": False, "load_status": "loading",
        "route_status": "loading", "stop_duration": 18, "last_movement": (datetime.utcnow() - timedelta(minutes=18)).isoformat(),
        "destination_eta": "2025-09-14T17:00:00", "route_progress": 3, "fuel_level": 92,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(minutes=25)).isoformat()
    },
    # Truck 16 - Normal operation
    {
        "id": 16, "vehicle_id": "OD-03-NT-1016", "driver_name": "Rakesh Swain", "driver_phone": "+91-9437123016",
        "license_plate": "OD-03-NT-1016", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9750, "longitude": 85.3200, "speed": 62, "heading": 88,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "on_route", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-14T15:50:00", "route_progress": 28, "fuel_level": 82,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(minutes=35)).isoformat()
    },
    # Truck 17 - At toll plaza
    {
        "id": 17, "vehicle_id": "OD-03-NT-1017", "driver_name": "Sanjay Mishra", "driver_phone": "+91-9437123017",
        "license_plate": "OD-03-NT-1017", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9900, "longitude": 85.5800, "speed": 0, "heading": 85,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "toll_payment", "stop_duration": 5, "last_movement": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
        "destination_eta": "2025-09-14T15:25:00", "route_progress": 62, "fuel_level": 66,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=1, minutes=25)).isoformat()
    },
    # Truck 18 - High speed
    {
        "id": 18, "vehicle_id": "OD-03-NT-1018", "driver_name": "Bijay Kumar", "driver_phone": "+91-9437123018",
        "license_plate": "OD-03-NT-1018", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.9800, "longitude": 85.6200, "speed": 92, "heading": 82,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "speed_violation", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-14T14:55:00", "route_progress": 72, "fuel_level": 54,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=1, minutes=40)).isoformat()
    },
    # Truck 19 - Approaching destination
    {
        "id": 19, "vehicle_id": "OD-03-NT-1019", "driver_name": "Pradeep Sahoo", "driver_phone": "+91-9437123019",
        "license_plate": "OD-03-NT-1019", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 20.8850, "longitude": 86.0600, "speed": 38, "heading": 85,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "approaching_destination", "stop_duration": 0, "last_movement": datetime.utcnow().isoformat(),
        "destination_eta": "2025-09-14T15:05:00", "route_progress": 95, "fuel_level": 42,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=2, minutes=15)).isoformat()
    },
    # Truck 20 - Emergency stop
    {
        "id": 20, "vehicle_id": "OD-03-NT-1020", "driver_name": "Dinesh Patra", "driver_phone": "+91-9437123020",
        "license_plate": "OD-03-NT-1020", "vehicle_type": "Heavy Truck (Coal)", "capacity_tons": 25,
        "latitude": 21.0100, "longitude": 85.5100, "speed": 0, "heading": 90,
        "timestamp": datetime.utcnow().isoformat(), "material_loaded": True, "load_status": "loaded",
        "route_status": "emergency_stop", "stop_duration": 3, "last_movement": (datetime.utcnow() - timedelta(minutes=3)).isoformat(),
        "destination_eta": "2025-09-14T15:35:00", "route_progress": 55, "fuel_level": 70,
        "gate_entry_logged": True, "last_gate_scan": (datetime.utcnow() - timedelta(hours=1, minutes=12)).isoformat()
    }
]

# Gas Stations along the route
GAS_STATIONS = [
    {"id": "HP_TALCHER", "name": "HP Petrol Pump", "latitude": 20.9500, "longitude": 85.2300, "brand": "HP", "services": ["Fuel", "Air", "Water"]},
    {"id": "IOC_BOINDA", "name": "Indian Oil Station", "latitude": 20.9720, "longitude": 85.2950, "brand": "Indian Oil", "services": ["Fuel", "Restaurant", "ATM"]},
    {"id": "BPCL_DHENKANAL", "name": "BPCL Fuel Station", "latitude": 20.9900, "longitude": 85.4100, "brand": "Bharat Petroleum", "services": ["Fuel", "Parking", "Toilet"]},
    {"id": "REL_KAMAKHYA", "name": "Reliance Petrol Pump", "latitude": 21.0080, "longitude": 85.5200, "brand": "Reliance", "services": ["Fuel", "Convenience Store"]},
    {"id": "HP_PARJANG", "name": "HP Highway Station", "latitude": 20.9850, "longitude": 85.6300, "brand": "HP", "services": ["Fuel", "Restaurant", "Rest Area"]},
    {"id": "IOC_BHUBAN", "name": "Indian Oil Bhuban", "latitude": 20.9180, "longitude": 85.8850, "brand": "Indian Oil", "services": ["Fuel", "Mechanic", "ATM"]},
    {"id": "BPCL_JAJPUR", "name": "BPCL Jajpur Road", "latitude": 20.8980, "longitude": 86.0180, "brand": "Bharat Petroleum", "services": ["Fuel", "Air", "Water"]}
]

# Toll Gates along the route
TOLL_GATES = [
    {"id": "DHENKANAL_TOLL", "name": "Dhenkanal Toll Plaza", "latitude": 20.9930, "longitude": 85.4300, "fee_heavy": 120, "operator": "NHAI"},
    {"id": "PARJANG_TOLL", "name": "Parjang Toll Plaza", "latitude": 20.9780, "longitude": 85.6100, "fee_heavy": 95, "operator": "NHAI"},
    {"id": "JAJPUR_TOLL", "name": "Jajpur Road Toll Plaza", "latitude": 20.8920, "longitude": 86.0050, "fee_heavy": 85, "operator": "NHAI"}
]

# Activity log storage
activity_log = []

# Storage for incidents and gate entries
pagerduty_incidents = []
gate_entries = []
escalation_tasks = {}  # Track active escalation tasks

# Mock gate entry data
gate_entries = [
    {
        "id": "GATE_001",
        "vehicle_id": "OD-03-NT-1001",
        "number_plate": "OD-03-NT-1001",
        "driver_name": "Rajesh Kumar",
        "entry_time": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "exit_time": None,
        "camera_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD//gA7Q1JFQVRPUjogZ2QtanBlZyB2MS4wICh1c2luZyBJSkcgSlBFRyB2NjIpLCBxdWFsaXR5ID0gODAK/9sAQwAIBgYHBgUIBwcHCQkICgwUDQwLCwwZEhMPFB0aHx4dGhwcICQuJyAiLCMcHCg3KSwwMTQ0NB8nOT04MjwuMzQy",
        "gate_officer": "Security Officer Raman Das",
        "load_weight": 24.5,
        "ai_confidence": 0.96
    }
]

# PagerDuty-style escalation functions
async def trigger_pagerduty_escalation(incident):
    """Trigger PagerDuty-style escalation: Push → Email → Phone calls every minute"""
    incident_id = incident["id"]
    
    # Start with level 1 contacts (primary on-call)
    level_1_contacts = [c for c in ESCALATION_CONTACTS if c["escalation_level"] == 1]
    
    logger.critical(f"🚨 PAGERDUTY ESCALATION STARTED:")
    logger.critical(f"   🆔 Incident: {incident_id}")
    logger.critical(f"   🚛 Vehicle: {incident['vehicle_id']}")
    logger.critical(f"   ⚠️  Type: {incident['incident_type'].upper()}")
    logger.critical(f"   📍 Location: {incident.get('location', {}).get('description', 'Unknown')}")
    logger.critical(f"   💬 Message: {incident['message']}")
    
    # Phase 1: Immediate push notifications to all level 1 contacts
    await send_push_notifications(level_1_contacts, incident)
    
    # Start escalation task
    escalation_tasks[incident_id] = asyncio.create_task(
        escalation_loop(incident, level_1_contacts)
    )

async def send_push_notifications(contacts, incident):
    """Send immediate push notifications"""
    for contact in contacts:
        logger.critical(f"📱 PUSH NOTIFICATION SENT:")
        logger.critical(f"   👤 To: {contact['name']}")
        logger.critical(f"   📲 Push Token: {contact['push_token']}")
        logger.critical(f"   📧 Email: {contact['email']}")
        logger.critical(f"   🚛 Vehicle: {incident['vehicle_id']}")
        logger.critical(f"   ⚠️  Alert: {incident['incident_type'].upper()}")
        logger.critical(f"   💬 Message: {incident['message']}")
        
        # Add to incident contact attempts
        contact_attempt = {
            "contact": contact['name'],
            "method": "push_notification",
            "timestamp": datetime.utcnow().isoformat(),
            "delivered": True
        }
        incident.setdefault("contact_attempts", []).append(contact_attempt)

async def escalation_loop(incident, contacts):
    """Main escalation loop following PagerDuty pattern"""
    incident_id = incident["id"]
    escalation_level = 1
    attempt_count = 0
    
    while not incident.get("acknowledged", False) and escalation_level <= 3:
        # Wait for escalation timeout
        timeout = contacts[0]["escalation_timeout"] if contacts else 5
        await asyncio.sleep(timeout * 60)  # Convert minutes to seconds for demo (should be 60)
        
        # Check if incident was acknowledged during wait
        if incident.get("acknowledged", False):
            logger.info(f"✅ Incident {incident_id} acknowledged, stopping escalation")
            break
        
        attempt_count += 1
        
        if attempt_count <= 3:
            # Phase 2: Email notifications
            await send_email_notifications(contacts, incident, attempt_count)
            await asyncio.sleep(60)  # Wait 1 minute
            
            if not incident.get("acknowledged", False):
                # Phase 3: Phone calls
                await make_phone_calls(contacts, incident, attempt_count)
        else:
            # Escalate to next level
            escalation_level += 1
            next_level_contacts = [c for c in ESCALATION_CONTACTS if c["escalation_level"] == escalation_level]
            
            if next_level_contacts:
                logger.critical(f"🔺 ESCALATING TO LEVEL {escalation_level}:")
                for contact in next_level_contacts:
                    logger.critical(f"   👤 Escalating to: {contact['name']} ({contact['role']})")
                
                contacts = next_level_contacts
                attempt_count = 0
                await send_push_notifications(next_level_contacts, incident)
            else:
                logger.critical(f"🚨 MAXIMUM ESCALATION REACHED - All contacts exhausted for incident {incident_id}")
                break

async def send_email_notifications(contacts, incident, attempt):
    """Send email notifications"""
    for contact in contacts:
        logger.critical(f"📧 EMAIL NOTIFICATION SENT (Attempt {attempt}):")
        logger.critical(f"   👤 To: {contact['name']}")
        logger.critical(f"   📧 Email: {contact['email']}")
        logger.critical(f"   🚛 Vehicle: {incident['vehicle_id']}")
        logger.critical(f"   ⚠️  Alert: {incident['incident_type'].upper()}")
        logger.critical(f"   💬 Message: {incident['message']}")
        logger.critical(f"   🕐 Timestamp: {datetime.utcnow().isoformat()}")
        
        contact_attempt = {
            "contact": contact['name'],
            "method": "email",
            "attempt": attempt,
            "timestamp": datetime.utcnow().isoformat(),
            "delivered": True
        }
        incident.setdefault("contact_attempts", []).append(contact_attempt)

async def make_phone_calls(contacts, incident, attempt):
    """Make phone calls"""
    for contact in contacts:
        logger.critical(f"📞 PHONE CALL INITIATED (Attempt {attempt}):")
        logger.critical(f"   👤 Calling: {contact['name']}")
        logger.critical(f"   📱 Phone: {contact['phone']}")
        logger.critical(f"   🚛 Vehicle: {incident['vehicle_id']}")
        logger.critical(f"   ⚠️  Alert: {incident['incident_type'].upper()}")
        logger.critical(f"   💬 Message: {incident['message']}")
        logger.critical(f"   📞 Call Status: {'ANSWERED' if random.random() > 0.7 else 'NO ANSWER'}")
        
        contact_attempt = {
            "contact": contact['name'],
            "method": "phone_call",
            "attempt": attempt,
            "timestamp": datetime.utcnow().isoformat(),
            "answered": random.random() > 0.7
        }
        incident.setdefault("contact_attempts", []).append(contact_attempt)

def simulate_smart_camera_scan(vehicle_id):
    """Simulate smart camera scanning vehicle number plate with AI confidence"""
    camera_data = {
        "camera_id": random.choice(["CAM_GATE_01", "CAM_GATE_02", "CAM_LOAD_01", "CAM_LOAD_02"]),
        "scan_time": datetime.utcnow().isoformat(),
        "number_plate_detected": vehicle_id,
        "confidence_score": random.uniform(0.85, 0.99),
        "image_quality": "HIGH" if random.random() > 0.2 else "MEDIUM",
        "detection_method": "OCR + AI + Deep Learning",
        "camera_location": f"NTPC Talcher - {random.choice(['Main Entry Gate', 'Secondary Gate', 'Loading Bay A', 'Loading Bay B'])}",
        "processing_time_ms": random.randint(150, 400),
        "plate_region": "Odisha, India",
        "vehicle_type_detected": "Heavy Commercial Vehicle"
    }
    
    logger.info(f"📷 SMART CAMERA AI SCAN:")
    logger.info(f"   🎯 Vehicle Detected: {vehicle_id}")
    logger.info(f"   📊 AI Confidence: {camera_data['confidence_score']:.2%}")
    logger.info(f"   📸 Quality: {camera_data['image_quality']}")
    logger.info(f"   🧠 AI Processing: {camera_data['processing_time_ms']}ms")
    logger.info(f"   📍 Location: {camera_data['camera_location']}")
    
    return camera_data

def check_critical_incidents_with_pagerduty(vehicle):
    """Enhanced incident detection with PagerDuty escalation"""
    incidents = []
    
    # Critical stop incident (>60 minutes) - triggers PagerDuty
    if vehicle["speed"] == 0 and vehicle["stop_duration"] > 60:
        incident = {
            "id": f"PD_CRITICAL_STOP_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
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
            "escalation_level": 1,
            "contact_attempts": [],
            "escalation_timeout": 5
        }
        incidents.append(incident)
    
    # Critical speed violation (>90 km/h) - triggers PagerDuty
    if vehicle["speed"] > 90:
        incident = {
            "id": f"PD_CRITICAL_SPEED_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
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
            "escalation_level": 1,
            "contact_attempts": [],
            "escalation_timeout": 5
        }
        incidents.append(incident)
    
    # Route deviation for extended period (>30 minutes) - triggers PagerDuty
    if not is_on_route(vehicle["latitude"], vehicle["longitude"])[0] and vehicle["stop_duration"] > 30:
        incident = {
            "id": f"PD_CRITICAL_DEVIATION_{vehicle['vehicle_id']}_{int(datetime.utcnow().timestamp())}",
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
            "escalation_level": 1,
            "contact_attempts": [],
            "escalation_timeout": 5
        }
        incidents.append(incident)
    
    return incidents

# Utility functions (keeping existing ones and adding new)
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
    for waypoint in ROUTE_WAYPOINTS:
        distance = calculate_distance(
            vehicle_lat, vehicle_lon,
            waypoint["latitude"], waypoint["longitude"]
        )
        if distance <= max_deviation:
            return True, waypoint["name"], distance
    return False, None, float('inf')

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

# API Routes
@app.get("/")
async def root():
    return {
        "message": "NTPC Fleet Management System - Enhanced India Operations",
        "version": "4.0.0",
        "status": "operational",
        "features": [
            "13 Heavy Coal Transport Trucks",
            "NTPC Talcher to Chandilkhol Route",
            "PagerDuty-style Critical Incident Escalation",
            "Smart Gate Camera with AI Recognition",
            "Real-time Push Notifications",
            "Multi-level Escalation (Push → Email → Phone)",
            "Enhanced Vehicle Tracking",
            "Gas Station & Toll Gate Mapping"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "total_vehicles": len(mock_vehicles),
        "critical_incidents": len([i for i in pagerduty_incidents if i.get("severity") == "critical"]),
        "active_escalations": len(escalation_tasks),
        "gate_cameras_active": len([c for c in PLANT_STOCKYARD["smart_cameras"] if c["active"]]),
        "pagerduty_integration": "operational"
    }

@app.get("/api/v1/vehicles/locations")
async def get_vehicle_locations():
    """Enhanced vehicle locations with PagerDuty incident detection"""
    global pagerduty_incidents
    
    for vehicle in mock_vehicles:
        # Simulate vehicle movement
        simulate_enhanced_vehicle_movement(vehicle)
        
        # Check for critical incidents that trigger PagerDuty
        new_incidents = check_critical_incidents_with_pagerduty(vehicle)
        for incident in new_incidents:
            # Check if this incident already exists
            existing = [i for i in pagerduty_incidents if 
                       i["vehicle_id"] == incident["vehicle_id"] and 
                       i["incident_type"] == incident["incident_type"] and 
                       not i.get("acknowledged", False)]
            
            if not existing:
                pagerduty_incidents.append(incident)
                
                # Trigger PagerDuty escalation
                asyncio.create_task(trigger_pagerduty_escalation(incident))
    
    return {
        "locations": mock_vehicles,
        "count": len(mock_vehicles)
    }

@app.get("/api/v1/incidents/pagerduty")
async def get_pagerduty_incidents():
    """Get all PagerDuty incidents with escalation status"""
    return {
        "incidents": pagerduty_incidents,
        "count": len(pagerduty_incidents),
        "active_escalations": len(escalation_tasks),
        "escalation_contacts": len(ESCALATION_CONTACTS)
    }

@app.get("/api/v1/gate/entries")
async def get_gate_entries():
    """Get gate entries from smart camera system"""
    return {
        "entries": gate_entries,
        "count": len(gate_entries),
        "active_cameras": len([c for c in PLANT_STOCKYARD["smart_cameras"] if c["active"]])
    }

@app.post("/api/v1/gate/scan/{vehicle_id}")
async def simulate_gate_scan(vehicle_id: str):
    """Simulate smart camera scanning a vehicle at gate with AI recognition"""
    # Find the vehicle
    vehicle = next((v for v in mock_vehicles if v["vehicle_id"] == vehicle_id), None)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Simulate AI camera scan
    camera_data = simulate_smart_camera_scan(vehicle_id)
    
    # Create gate entry record with AI confidence
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
        "ai_confidence": camera_data["confidence_score"],
        "camera_scan_data": camera_data
    }
    
    gate_entries.append(gate_entry)
    
    # Update vehicle gate tracking
    vehicle["gate_entry_logged"] = True
    vehicle["last_gate_scan"] = datetime.utcnow().isoformat()
    
    return {
        "message": f"Smart gate scan completed for vehicle {vehicle_id}",
        "gate_entry": gate_entry,
        "camera_data": camera_data
    }

@app.post("/api/v1/incidents/{incident_id}/acknowledge")
async def acknowledge_pagerduty_incident(incident_id: str):
    """Acknowledge PagerDuty incident and stop escalation"""
    for incident in pagerduty_incidents:
        if incident["id"] == incident_id:
            incident["acknowledged"] = True
            incident["acknowledged_at"] = datetime.utcnow().isoformat()
            
            # Stop escalation task
            if incident_id in escalation_tasks:
                escalation_tasks[incident_id].cancel()
                del escalation_tasks[incident_id]
            
            logger.critical(f"✅ PAGERDUTY INCIDENT ACKNOWLEDGED:")
            logger.critical(f"   🆔 ID: {incident_id}")
            logger.critical(f"   🚛 Vehicle: {incident['vehicle_id']}")
            logger.critical(f"   ⚠️  Type: {incident['incident_type']}")
            logger.critical(f"   🛑 Escalation stopped")
            
            return {"message": "PagerDuty incident acknowledged and escalation stopped", "incident": incident}
    
    raise HTTPException(status_code=404, detail="Incident not found")

@app.get("/api/v1/escalation/status")
async def get_escalation_status():
    """Get current escalation status"""
    return {
        "active_escalations": len(escalation_tasks),
        "escalation_contacts": ESCALATION_CONTACTS,
        "total_contacts": len(ESCALATION_CONTACTS),
        "current_incidents": len([i for i in pagerduty_incidents if not i.get("acknowledged", False)])
    }

@app.get("/api/v1/cameras/status")
async def get_camera_status():
    """Get smart camera system status"""
    return {
        "cameras": PLANT_STOCKYARD["smart_cameras"],
        "total_cameras": len(PLANT_STOCKYARD["smart_cameras"]),
        "active_cameras": len([c for c in PLANT_STOCKYARD["smart_cameras"] if c["active"]]),
        "ai_enabled_cameras": len([c for c in PLANT_STOCKYARD["smart_cameras"] if c.get("ai_enabled", False)]),
        "last_scan": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/analytics/summary")
async def get_analytics_summary():
    """Get comprehensive 8-panel analytics dashboard data"""
    
    # Calculate analytics from all 13 vehicles
    on_route = len([v for v in mock_vehicles if v["route_status"] == "on_route"])
    stopped = len([v for v in mock_vehicles if v["speed"] == 0])
    critical_alerts = len([v for v in mock_vehicles if v["route_status"] in ["critical_stop", "critical_speed"]])
    speed_violations = len([v for v in mock_vehicles if v["route_status"] in ["speed_violation", "critical_speed"]])
    low_fuel = len([v for v in mock_vehicles if v["fuel_level"] < 30])
    route_deviations = len([v for v in mock_vehicles if v["route_status"] == "deviation"])
    
    avg_fuel = sum(v["fuel_level"] for v in mock_vehicles) / len(mock_vehicles)
    avg_progress = sum(v["route_progress"] for v in mock_vehicles) / len(mock_vehicles)
    
    return {
        "total_vehicles": len(mock_vehicles),
        "vehicles_on_route": on_route,
        "vehicles_stopped": stopped,
        "critical_alerts": critical_alerts,
        "speed_violations": speed_violations,
        "low_fuel_vehicles": low_fuel,
        "route_deviations": route_deviations,
        "avg_fuel_level": round(avg_fuel, 1),
        "avg_route_progress": round(avg_progress, 1),
        "active_pagerduty_incidents": len([i for i in pagerduty_incidents if not i.get("acknowledged", False)]),
        "total_gas_stations": len(GAS_STATIONS),
        "total_toll_gates": len(TOLL_GATES),
        "gate_entries_today": len(gate_entries),
        "last_updated": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/gas-stations")
async def get_gas_stations():
    """Get all gas stations along the route"""
    return {
        "gas_stations": GAS_STATIONS,
        "count": len(GAS_STATIONS),
        "brands": list(set(gs["brand"] for gs in GAS_STATIONS))
    }

@app.get("/api/v1/toll-gates")
async def get_toll_gates():
    """Get all toll gates along the route"""
    return {
        "toll_gates": TOLL_GATES,
        "count": len(TOLL_GATES),
        "total_fee_heavy": sum(tg["fee_heavy"] for tg in TOLL_GATES)
    }

@app.get("/api/v1/activity-log")
async def get_activity_log():
    """Get real-time activity log"""
    return {
        "activities": activity_log[-50:],  # Last 50 activities
        "count": len(activity_log),
        "last_updated": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/fuel/recommendations/{vehicle_id}")
async def get_fuel_recommendations(vehicle_id: str):
    """Get nearest gas station recommendations for low fuel vehicles"""
    vehicle = next((v for v in mock_vehicles if v["vehicle_id"] == vehicle_id), None)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    if vehicle["fuel_level"] > 30:
        return {"message": "Vehicle has sufficient fuel", "fuel_level": vehicle["fuel_level"]}
    
    # Find nearest gas stations
    vehicle_lat, vehicle_lng = vehicle["latitude"], vehicle["longitude"]
    nearest_stations = []
    
    for station in GAS_STATIONS:
        distance = calculate_distance(vehicle_lat, vehicle_lng, station["latitude"], station["longitude"])
        station_with_distance = {**station, "distance_km": round(distance / 1000, 1)}
        nearest_stations.append(station_with_distance)
    
    # Sort by distance and take top 3
    nearest_stations.sort(key=lambda x: x["distance_km"])
    
    return {
        "vehicle_id": vehicle_id,
        "current_fuel": vehicle["fuel_level"],
        "status": "LOW_FUEL_ALERT" if vehicle["fuel_level"] < 15 else "FUEL_ADVISORY",
        "recommended_stations": nearest_stations[:3],
        "total_stations_available": len(GAS_STATIONS)
    }

def generate_mock_camera_image():
    """Generate mock base64 camera image"""
    return "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD//gA7Q1JFQVRPUjogZ2QtanBlZyB2MS4wICh1c2luZyBJSkcgSlBFRyB2NjIpLCBxdWFsaXR5ID0gODAK/9sAQwAIBgYHBgUIBwcHCQkICgwUDQwLCwwZEhMPFB0aHx4dGhwcICQuJyAiLCMcHCg3KSwwMTQ0NB8nOT04MjwuMzQy"

def log_activity(vehicle_id, activity_type, message, severity="info"):
    """Log vehicle activity for real-time monitoring"""
    activity = {
        "id": f"ACT_{len(activity_log) + 1:05d}",
        "timestamp": datetime.utcnow().isoformat(),
        "vehicle_id": vehicle_id,
        "activity_type": activity_type,
        "message": message,
        "severity": severity,
        "location": get_nearest_landmark(
            next(v["latitude"] for v in mock_vehicles if v["vehicle_id"] == vehicle_id),
            next(v["longitude"] for v in mock_vehicles if v["vehicle_id"] == vehicle_id)
        )
    }
    activity_log.append(activity)
    
    # Keep only last 1000 activities
    if len(activity_log) > 1000:
        activity_log.pop(0)

def simulate_enhanced_vehicle_movement(vehicle):
    """Enhanced vehicle simulation with realistic behavior and activity logging"""
    old_status = vehicle["route_status"]
    old_speed = vehicle["speed"]
    old_fuel = vehicle["fuel_level"]
    
    if vehicle["route_status"] == "on_route" and vehicle["speed"] > 0:
        progress = vehicle["route_progress"]
        if progress < 100:
            base_progress = random.uniform(0.3, 1.5)
            vehicle["route_progress"] = min(progress + base_progress, 100)
            
            # Update position along route
            if vehicle["route_progress"] < 100:
                vehicle["latitude"] += random.uniform(-0.0001, 0.0001)
                vehicle["longitude"] += random.uniform(-0.0001, 0.0001)
    
    # Add realistic variation
    if vehicle["speed"] > 0:
        vehicle["speed"] = max(0, vehicle["speed"] + random.uniform(-8, 8))
        vehicle["fuel_level"] = max(0, vehicle["fuel_level"] - random.uniform(0.1, 0.3))
    
    # Update stop duration and status
    if vehicle["speed"] == 0:
        last_movement = datetime.fromisoformat(vehicle["last_movement"].replace('Z', '+00:00'))
        vehicle["stop_duration"] = int((datetime.utcnow() - last_movement.replace(tzinfo=None)).total_seconds() / 60)
        
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
    
    # Log significant changes
    if old_status != vehicle["route_status"]:
        if vehicle["route_status"] == "critical_stop":
            log_activity(vehicle["vehicle_id"], "CRITICAL_STOP", 
                        f"Vehicle stopped for {vehicle['stop_duration']} minutes", "critical")
        elif vehicle["route_status"] == "critical_speed":
            log_activity(vehicle["vehicle_id"], "SPEED_VIOLATION", 
                        f"Critical speed violation: {vehicle['speed']:.1f} km/h", "critical")
        elif vehicle["route_status"] == "speed_violation":
            log_activity(vehicle["vehicle_id"], "SPEED_WARNING", 
                        f"Speed limit exceeded: {vehicle['speed']:.1f} km/h", "warning")
        elif vehicle["route_status"] == "on_route" and old_status in ["critical_stop", "critical_speed"]:
            log_activity(vehicle["vehicle_id"], "RESUMED_ROUTE", 
                        f"Vehicle resumed normal operation", "info")
    
    # Log fuel alerts
    if vehicle["fuel_level"] < 15 and old_fuel >= 15:
        log_activity(vehicle["vehicle_id"], "LOW_FUEL_CRITICAL", 
                    f"Critical fuel level: {vehicle['fuel_level']:.1f}%", "critical")
    elif vehicle["fuel_level"] < 30 and old_fuel >= 30:
        log_activity(vehicle["vehicle_id"], "LOW_FUEL_WARNING", 
                    f"Low fuel warning: {vehicle['fuel_level']:.1f}%", "warning")
    
    vehicle["timestamp"] = datetime.utcnow().isoformat()

# Background monitoring with PagerDuty integration
async def enhanced_incident_monitoring():
    """Enhanced background monitoring with PagerDuty escalation"""
    while True:
        try:
            for vehicle in mock_vehicles:
                incidents = check_critical_incidents_with_pagerduty(vehicle)
                for incident in incidents:
                    existing = [i for i in pagerduty_incidents if 
                              i["vehicle_id"] == incident["vehicle_id"] and 
                              i["incident_type"] == incident["incident_type"] and 
                              not i.get("acknowledged", False)]
                    
                    if not existing:
                        pagerduty_incidents.append(incident)
                        
                        # Start PagerDuty escalation
                        asyncio.create_task(trigger_pagerduty_escalation(incident))
            
            await asyncio.sleep(8)  # Check every 8 seconds as required
        except Exception as e:
            logger.error(f"Error in enhanced incident monitoring: {e}")
            await asyncio.sleep(60)

@app.post("/api/v1/mobile/demo-alert")
async def send_mobile_demo_alert(alert_data: dict):
    """Send a demo mobile alert for demonstration purposes"""
    logger.info("📱 MOBILE DEMO ALERT TRIGGERED:")
    logger.info(f"   🚛 Vehicle: {alert_data.get('vehicle_id')}")
    logger.info(f"   👤 Driver: {alert_data.get('driver_name')} ({alert_data.get('driver_phone')})")
    logger.info(f"   ⚠️  Incident: {alert_data.get('incident_type')}")
    logger.info(f"   📍 Location: {alert_data.get('location')}")
    logger.info(f"   🚨 Details: Speed {alert_data.get('speed')} - Critical Violation")
    logger.info(f"   📱 Mobile Push: Sending to all stakeholder devices")
    logger.info(f"   📧 Email Alert: Dispatching emergency notifications")
    logger.info(f"   📞 SMS Alert: Sending to emergency contacts")
    
    # Simulate mobile notification dispatch
    mobile_contacts = [
        {"name": "Fleet Manager", "phone": "+91-9437100001", "role": "PRIMARY"},
        {"name": "IT Emergency", "phone": "+91-9437100002", "role": "TECH"},
        {"name": "Operations Control", "phone": "+91-9437100003", "role": "OPERATIONS"},
        {"name": "Safety Team", "phone": "+91-9437100004", "role": "SAFETY"}
    ]
    
    for contact in mobile_contacts:
        logger.critical(f"📱 MOBILE NOTIFICATION SENT:")
        logger.critical(f"   👤 To: {contact['name']} ({contact['role']})")
        logger.critical(f"   📱 Phone: {contact['phone']}")
        logger.critical(f"   🚛 Alert: {alert_data.get('vehicle_id')} - Speed Violation")
        logger.critical(f"   📍 Location: {alert_data.get('location')}")
        logger.critical(f"   💬 Message: Critical speed violation detected - {alert_data.get('speed')}")
        logger.critical(f"   ⏰ Timestamp: {alert_data.get('timestamp')}")
        logger.critical(f"   🔴 Priority: {alert_data.get('severity').upper()}")
    
    return {
        "status": "success",
        "message": "Mobile demo alert sent successfully",
        "alert_data": alert_data,
        "notifications_sent": len(mobile_contacts),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(enhanced_incident_monitoring())
    logger.info("🚨 NTPC Enhanced Fleet Management System Started")
    logger.info("📟 PagerDuty-style escalation system: ACTIVE")
    logger.info("📷 Smart gate cameras with AI: OPERATIONAL")
    logger.info(f"🎯 Active cameras: {len([c for c in PLANT_STOCKYARD['smart_cameras'] if c['active']])}")
    logger.info(f"👥 Escalation contacts: {len(ESCALATION_CONTACTS)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006, reload=True)
