import random
import time
from datetime import datetime, timedelta
from typing import List, Dict


class MockDataService:
    """Mock service to generate sample fleet data for demonstration"""
    
    def __init__(self):
        # NYC area coordinates for demonstration
        self.base_lat = 40.7128
        self.base_lng = -74.0060
        self.vehicles = [
            {
                "vehicle_id": "TRUCK001",
                "driver_name": "John Smith",
                "license_plate": "NY-1234",
                "vehicle_type": "Heavy Truck"
            },
            {
                "vehicle_id": "TRUCK002", 
                "driver_name": "Sarah Johnson",
                "license_plate": "NY-5678",
                "vehicle_type": "Delivery Van"
            },
            {
                "vehicle_id": "TRUCK003",
                "driver_name": "Mike Wilson",
                "license_plate": "NY-9012", 
                "vehicle_type": "Container Truck"
            },
            {
                "vehicle_id": "TRUCK004",
                "driver_name": "Emma Davis",
                "license_plate": "NY-3456",
                "vehicle_type": "Flatbed Truck"
            },
            {
                "vehicle_id": "TRUCK005",
                "driver_name": "Robert Brown",
                "license_plate": "NY-7890",
                "vehicle_type": "Tanker Truck"
            }
        ]
        
        # Initialize vehicle positions
        self.vehicle_positions = {}
        for vehicle in self.vehicles:
            self.vehicle_positions[vehicle["vehicle_id"]] = {
                "lat": self.base_lat + random.uniform(-0.02, 0.02),
                "lng": self.base_lng + random.uniform(-0.02, 0.02),
                "speed": random.uniform(0, 80),
                "heading": random.uniform(0, 360),
                "last_update": datetime.utcnow()
            }

    def get_all_vehicle_locations(self) -> List[Dict]:
        """Generate mock vehicle location data"""
        locations = []
        
        for vehicle in self.vehicles:
            vehicle_id = vehicle["vehicle_id"]
            
            # Update position slightly (simulate movement)
            current_pos = self.vehicle_positions[vehicle_id]
            
            # Simulate realistic movement
            if random.random() > 0.7:  # 30% chance to move
                lat_change = random.uniform(-0.001, 0.001)
                lng_change = random.uniform(-0.001, 0.001)
                current_pos["lat"] += lat_change
                current_pos["lng"] += lng_change
                current_pos["speed"] = random.uniform(0, 90)
                current_pos["heading"] = random.uniform(0, 360)
                current_pos["last_update"] = datetime.utcnow()
            
            # Create location data
            location = {
                "vehicle_id": vehicle_id,
                "latitude": current_pos["lat"],
                "longitude": current_pos["lng"],
                "speed": current_pos["speed"],
                "heading": current_pos["heading"],
                "altitude": random.uniform(0, 100),
                "accuracy": random.uniform(1, 10),
                "timestamp": current_pos["last_update"].isoformat(),
                "driver_name": vehicle["driver_name"],
                "license_plate": vehicle["license_plate"],
                "vehicle_type": vehicle["vehicle_type"]
            }
            
            locations.append(location)
        
        return locations

    def get_vehicles(self) -> List[Dict]:
        """Get list of vehicles"""
        return self.vehicles.copy()

    def get_vehicle_location(self, vehicle_id: str) -> Dict:
        """Get specific vehicle location"""
        locations = self.get_all_vehicle_locations()
        for location in locations:
            if location["vehicle_id"] == vehicle_id:
                return location
        return None

    def simulate_geofence_event(self) -> Dict:
        """Simulate a random geofence event"""
        vehicle = random.choice(self.vehicles)
        event_type = random.choice(["enter", "exit"])
        
        return {
            "vehicle_id": vehicle["vehicle_id"],
            "event_type": event_type,
            "latitude": self.base_lat + random.uniform(-0.005, 0.005),
            "longitude": self.base_lng + random.uniform(-0.005, 0.005),
            "geofence_name": "Plant Gate",
            "timestamp": datetime.utcnow().isoformat(),
            "notification_sent": True
        }


# Create singleton instance
mock_data_service = MockDataService()

