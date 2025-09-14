import httpx
import json
import firebase_admin
from firebase_admin import credentials, messaging
from typing import List, Dict, Optional
from ..core.config import settings
from ..models.vehicle import GeofenceEvent
import logging
import os

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.slack_webhook_url = settings.slack_webhook_url
        self.fcm_initialized = False
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self._init_firebase()

    def _init_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if settings.fcm_service_account_key and os.path.exists(settings.fcm_service_account_key):
                if not firebase_admin._apps:
                    cred = credentials.Certificate(settings.fcm_service_account_key)
                    firebase_admin.initialize_app(cred, {
                        'projectId': settings.fcm_project_id,
                    })
                self.fcm_initialized = True
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                logger.warning("Firebase service account key not found, FCM notifications disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")

    async def send_slack_notification(self, message: str, vehicle_id: str, event_type: str) -> bool:
        """Send notification to Slack webhook"""
        if not self.slack_webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        try:
            # Create rich Slack message
            slack_payload = {
                "text": f"Fleet Management Alert: {message}",
                "attachments": [
                    {
                        "color": "good" if event_type == "enter" else "warning",
                        "fields": [
                            {
                                "title": "Vehicle ID",
                                "value": vehicle_id,
                                "short": True
                            },
                            {
                                "title": "Event Type",
                                "value": event_type.capitalize(),
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": "<!date^{timestamp}^{date_short_pretty} at {time_secs}|{timestamp}>".format(
                                    timestamp=int(datetime.utcnow().timestamp())
                                ),
                                "short": True
                            }
                        ],
                        "footer": "Fleet Management System",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }

            response = await self.http_client.post(
                self.slack_webhook_url,
                json=slack_payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                logger.info(f"Slack notification sent successfully for vehicle {vehicle_id}")
                return True
            else:
                logger.error(f"Failed to send Slack notification: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return False

    async def send_fcm_notification(self, title: str, body: str, data: Dict = None) -> bool:
        """Send Firebase Cloud Messaging notification"""
        if not self.fcm_initialized:
            logger.warning("FCM not initialized, skipping notification")
            return False

        try:
            # Create FCM message
            message_data = data or {}
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=message_data,
                topic="fleet_updates"  # Send to topic, you can also send to specific tokens
            )

            # Send the message
            response = messaging.send(message)
            logger.info(f"FCM notification sent successfully: {response}")
            return True

        except Exception as e:
            logger.error(f"Error sending FCM notification: {str(e)}")
            return False

    async def send_geofence_notification(self, event: GeofenceEvent) -> Dict[str, bool]:
        """Send notifications for geofence events"""
        action = "entered" if event.event_type == "enter" else "exited"
        message = f"Vehicle {event.vehicle_id} has {action} the {event.geofence_name} area"
        
        # Send Slack notification
        slack_success = await self.send_slack_notification(
            message=message,
            vehicle_id=event.vehicle_id,
            event_type=event.event_type
        )

        # Send FCM notification
        fcm_title = f"Fleet Alert - {event.geofence_name}"
        fcm_data = {
            "vehicle_id": event.vehicle_id,
            "event_type": event.event_type,
            "geofence_name": event.geofence_name,
            "latitude": str(event.latitude),
            "longitude": str(event.longitude),
            "timestamp": event.timestamp.isoformat()
        }
        
        fcm_success = await self.send_fcm_notification(
            title=fcm_title,
            body=message,
            data=fcm_data
        )

        return {
            "slack_sent": slack_success,
            "fcm_sent": fcm_success
        }

    async def send_speed_alert(self, vehicle_id: str, speed: float, speed_limit: float = 80.0) -> Dict[str, bool]:
        """Send notifications for speed violations"""
        message = f"Vehicle {vehicle_id} is exceeding speed limit: {speed:.1f} km/h (limit: {speed_limit:.1f} km/h)"
        
        slack_success = await self.send_slack_notification(
            message=message,
            vehicle_id=vehicle_id,
            event_type="speed_alert"
        )

        fcm_success = await self.send_fcm_notification(
            title="Speed Alert",
            body=message,
            data={
                "vehicle_id": vehicle_id,
                "current_speed": str(speed),
                "speed_limit": str(speed_limit),
                "alert_type": "speed_violation"
            }
        )

        return {
            "slack_sent": slack_success,
            "fcm_sent": fcm_success
        }

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Import datetime here to avoid circular imports
from datetime import datetime

# Create a singleton instance
notification_service = NotificationService()

