"""
MQTT Handler Service for IoT sensor communication.
"""
import json
import logging
import threading
from typing import Dict, Any, Callable
import paho.mqtt.client as mqtt
from django.conf import settings
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


class MQTTHandler:
    """Handle MQTT communication with IoT sensors."""
    
    def __init__(self):
        self.client = mqtt.Client()
        self.channel_layer = get_channel_layer()
        self.connected = False
        self.topics = {
            settings.MQTT_TOPIC_SENSOR_DATA: self.handle_sensor_data,
            settings.MQTT_TOPIC_ALERTS: self.handle_alert_message,
            settings.MQTT_TOPIC_COMMANDS: self.handle_command_response,
        }
        
        # Setup callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        
    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client.connect(
                settings.MQTT_BROKER_HOST,
                settings.MQTT_BROKER_PORT,
                settings.MQTT_KEEPALIVE
            )
            self.client.loop_start()
            logger.info(f"Connected to MQTT broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            self.connected = True
            logger.info("Successfully connected to MQTT broker")
            
            # Subscribe to topics
            for topic in self.topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker with result code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker with result code: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for when the client subscribes to a topic."""
        logger.info(f"Successfully subscribed with QoS: {granted_qos}")
    
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received."""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            logger.debug(f"Received message on topic {topic}: {payload}")
            
            # Route to appropriate handler based on topic pattern
            for topic_pattern, handler in self.topics.items():
                if mqtt.topic_matches_sub(topic_pattern, topic):
                    handler(topic, payload)
                    break
            else:
                logger.warning(f"No handler found for topic: {topic}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON payload: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def handle_sensor_data(self, topic: str, payload: Dict[str, Any]):
        """Handle sensor data messages."""
        try:
            # Extract sensor ID from topic
            # Topic format: waste-wise/sensors/{sensor_id}/data
            parts = topic.split('/')
            sensor_id = parts[2] if len(parts) > 2 else None
            
            if not sensor_id:
                logger.error("Could not extract sensor ID from topic")
                return
            
            # Process sensor data
            from apps.sensors.tasks import process_sensor_reading
            process_sensor_reading.delay(sensor_id, payload)
            
            # Send real-time update via WebSocket
            self.send_websocket_update('sensor_update', {
                'sensor_id': sensor_id,
                'data': payload,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling sensor data: {e}")
    
    def handle_alert_message(self, topic: str, payload: Dict[str, Any]):
        """Handle alert messages from sensors."""
        try:
            # Process alert
            from apps.alerts.tasks import process_sensor_alert
            process_sensor_alert.delay(payload)
            
            # Send real-time alert via WebSocket
            self.send_websocket_update('alert_notification', {
                'alert': payload,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling alert message: {e}")
    
    def handle_command_response(self, topic: str, payload: Dict[str, Any]):
        """Handle command response from sensors."""
        try:
            # Extract sensor ID from topic
            parts = topic.split('/')
            sensor_id = parts[2] if len(parts) > 2 else None
            
            if not sensor_id:
                logger.error("Could not extract sensor ID from topic")
                return
            
            # Log command response
            logger.info(f"Command response from {sensor_id}: {payload}")
            
            # Send response via WebSocket
            self.send_websocket_update('command_response', {
                'sensor_id': sensor_id,
                'response': payload,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling command response: {e}")
    
    def publish(self, topic: str, payload: Dict[str, Any], qos: int = 1):
        """Publish a message to a topic."""
        try:
            message = json.dumps(payload)
            result = self.client.publish(topic, message, qos=qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published message to {topic}")
            else:
                logger.error(f"Failed to publish message to {topic}: {result.rc}")
                
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
    
    def send_command(self, sensor_id: str, command: str, parameters: Dict[str, Any] = None):
        """Send a command to a specific sensor."""
        topic = f"waste-wise/commands/{sensor_id}"
        payload = {
            'command': command,
            'parameters': parameters or {},
            'timestamp': timezone.now().isoformat()
        }
        self.publish(topic, payload)
    
    def send_websocket_update(self, event_type: str, data: Dict[str, Any]):
        """Send update via WebSocket to connected clients."""
        try:
            async_to_sync(self.channel_layer.group_send)(
                'sensor_updates',
                {
                    'type': 'sensor_message',
                    'event': event_type,
                    'data': data
                }
            )
        except Exception as e:
            logger.error(f"Error sending WebSocket update: {e}")


# Global MQTT handler instance
mqtt_handler = None


def get_mqtt_handler():
    """Get or create the global MQTT handler instance."""
    global mqtt_handler
    if mqtt_handler is None:
        mqtt_handler = MQTTHandler()
    return mqtt_handler


def start_mqtt_handler():
    """Start the MQTT handler."""
    handler = get_mqtt_handler()
    if not handler.connected:
        handler.connect()
    return handler


def stop_mqtt_handler():
    """Stop the MQTT handler."""
    global mqtt_handler
    if mqtt_handler and mqtt_handler.connected:
        mqtt_handler.disconnect()
        mqtt_handler = None