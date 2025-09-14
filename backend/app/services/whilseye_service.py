import httpx
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


class WhilseyeService:
    def __init__(self):
        self.api_url = settings.whilseye_api_url
        self.username = settings.whilseye_username
        self.password = settings.whilseye_password
        self.api_key = settings.whilseye_api_key
        self.access_token = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def authenticate(self) -> bool:
        """Authenticate with WHILSEYE API and get access token"""
        try:
            auth_data = {
                "username": self.username,
                "password": self.password,
                "api_key": self.api_key
            }
            
            response = await self.client.post(
                f"{self.api_url}/auth/login",
                json=auth_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                logger.info("Successfully authenticated with WHILSEYE API")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False

    async def get_vehicles(self) -> List[Dict]:
        """Get list of all vehicles from WHILSEYE API"""
        if not self.access_token:
            await self.authenticate()
            
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = await self.client.get(
                f"{self.api_url}/vehicles",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json().get("vehicles", [])
            elif response.status_code == 401:
                # Token expired, re-authenticate
                await self.authenticate()
                return await self.get_vehicles()
            else:
                logger.error(f"Failed to get vehicles: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting vehicles: {str(e)}")
            return []

    async def get_vehicle_location(self, vehicle_id: str) -> Optional[Dict]:
        """Get current location of a specific vehicle"""
        if not self.access_token:
            await self.authenticate()
            
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = await self.client.get(
                f"{self.api_url}/vehicles/{vehicle_id}/location",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                await self.authenticate()
                return await self.get_vehicle_location(vehicle_id)
            else:
                logger.error(f"Failed to get vehicle location: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting vehicle location: {str(e)}")
            return None

    async def get_all_vehicle_locations(self) -> List[Dict]:
        """Get current locations of all vehicles"""
        vehicles = await self.get_vehicles()
        locations = []
        
        for vehicle in vehicles:
            vehicle_id = vehicle.get("id") or vehicle.get("vehicle_id")
            if vehicle_id:
                location = await self.get_vehicle_location(vehicle_id)
                if location:
                    # Standardize the location data format
                    standardized_location = {
                        "vehicle_id": vehicle_id,
                        "latitude": location.get("lat") or location.get("latitude"),
                        "longitude": location.get("lng") or location.get("longitude"),
                        "speed": location.get("speed", 0.0),
                        "heading": location.get("heading") or location.get("bearing", 0.0),
                        "altitude": location.get("altitude", 0.0),
                        "accuracy": location.get("accuracy", 0.0),
                        "timestamp": location.get("timestamp") or datetime.utcnow().isoformat(),
                        "driver_name": vehicle.get("driver_name"),
                        "license_plate": vehicle.get("license_plate"),
                        "vehicle_type": vehicle.get("vehicle_type")
                    }
                    locations.append(standardized_location)
                    
        return locations

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Create a singleton instance
whilseye_service = WhilseyeService()

